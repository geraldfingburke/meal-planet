import asyncio
import json
import uuid

import dramatiq

from app.tasks import redis_broker  # noqa: F401 — ensures broker is set


@dramatiq.actor
def parse_recipe_task(job_id: str, url: str):
    """Background task: parse a recipe from URL and save to DB."""
    asyncio.run(_parse_and_save(job_id, url))


async def _parse_and_save(job_id: str, url: str):
    from app.database import worker_session
    from app.models.ingredient import Ingredient
    from app.models.recipe import Recipe, RecipeIngredient
    from app.services.family_service import get_default_family_id
    from app.services.recipe_parser import parse_recipe_from_url

    try:
        parsed = await parse_recipe_from_url(url)

        ingredient_ids = []
        seen_ingredient_ids = set()

        async with worker_session() as db:
            from sqlalchemy import select

            # Skip if a recipe with this URL already exists
            existing = await db.execute(
                select(Recipe).where(Recipe.source_url == parsed.source_url)
            )
            if existing.scalar_one_or_none():
                from app.services.job_service import update_job_status
                await update_job_status(
                    db, uuid.UUID(job_id), "completed",
                    {"error": "Recipe already imported", "duplicate": True},
                )
                return

            family_id = await get_default_family_id(db)

            recipe = Recipe(
                family_id=family_id,
                title=parsed.title,
                instructions=parsed.instructions,
                source_url=parsed.source_url,
                base_servings=parsed.base_servings,
                image_url=parsed.image_url,
                category=parsed.category,
            )
            db.add(recipe)
            await db.flush()

            # Save tags
            for tag_name in parsed.tags:
                tag_name = tag_name.strip().lower()
                if not tag_name:
                    continue
                from app.models.recipe import RecipeTag, Tag
                tag_result = await db.execute(
                    select(Tag).where(Tag.name == tag_name)
                )
                tag = tag_result.scalar_one_or_none()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                    await db.flush()
                db.add(RecipeTag(recipe_id=recipe.id, tag_id=tag.id))

            for pi in parsed.ingredients:
                from sqlalchemy import select

                result = await db.execute(
                    select(Ingredient).where(Ingredient.name.ilike(pi.name.strip()))
                )
                ingredient = result.scalar_one_or_none()
                if not ingredient:
                    ingredient = Ingredient(name=pi.name.strip())
                    db.add(ingredient)
                    await db.flush()

                # Skip duplicate ingredient for same recipe (merge by keeping first)
                if str(ingredient.id) in seen_ingredient_ids:
                    continue
                seen_ingredient_ids.add(str(ingredient.id))

                ri = RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ingredient.id,
                    quantity=pi.quantity,
                    unit=pi.unit,
                    walmart_search_term=getattr(pi, "walmart_search_term", None),
                )
                db.add(ri)
                ingredient_ids.append(str(ingredient.id))

            await db.commit()
            recipe_id = str(recipe.id)

        # Update job status in a separate session
        async with worker_session() as db:
            from app.services.job_service import update_job_status
            await update_job_status(
                db,
                uuid.UUID(job_id),
                "completed",
                {"recipe_id": recipe_id},
            )

        # Trigger Walmart price scraping for imported ingredients
        if ingredient_ids:
            from app.services.job_service import create_job
            async with worker_session() as db:
                price_job = await create_job(
                    db, "walmart_scrape", {"ingredient_count": len(ingredient_ids)}
                )
            from app.tasks.walmart_scraper import scrape_walmart_prices_task
            scrape_walmart_prices_task.send(str(price_job.id), ingredient_ids, recipe_id)
    except Exception as e:
        async with worker_session() as db:
            from app.services.job_service import update_job_status
            await update_job_status(
                db,
                uuid.UUID(job_id),
                "failed",
                {"error": str(e)},
            )
