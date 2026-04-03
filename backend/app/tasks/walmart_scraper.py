import asyncio
import uuid

import dramatiq
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings
from app.tasks import redis_broker  # noqa: F401


# -- Pydantic schema for Gemini pricing output ---------------------

class GeminiPriceItem(BaseModel):
    ingredient_id: str
    estimated_price: float


class GeminiPricingOutput(BaseModel):
    prices: list[GeminiPriceItem]


_PRICING_SYSTEM_INSTRUCTION = """\
You are a grocery price estimation engine for Walmart (US).

You will be given a JSON list of ingredients, each with an id and a walmart_search_term.
For each ingredient, estimate the current Walmart price in USD for a typical single
package/unit that a home cook would buy.

Return ONLY a JSON object matching this schema (no markdown, no commentary):

{
  "prices": [
    {
      "ingredient_id": "uuid-string - echo back the id you received",
      "estimated_price": number - estimated Walmart price in USD (e.g. 3.47)
    }
  ]
}

Rules:
- Use realistic current US Walmart prices (2025-2026 pricing).
- Prefer Great Value / store brand pricing when the search term suggests it.
- For produce sold by weight, estimate the price of a typical purchase quantity.
- Round to 2 decimal places.
- Return a price for EVERY ingredient in the input.
"""


@dramatiq.actor
def scrape_walmart_prices_task(job_id: str, ingredient_ids: list[str], recipe_id: str | None = None):
    """Background task: estimate Walmart prices for ingredients via Gemini."""
    asyncio.run(_estimate_prices(job_id, ingredient_ids, recipe_id))


async def _estimate_prices(job_id: str, ingredient_ids: list[str], recipe_id: str | None = None):
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from app.database import worker_session
    from app.models.ingredient import Ingredient
    from app.models.recipe import Recipe, RecipeIngredient
    from app.models.store_mapping import StoreMapping
    from app.services.job_service import update_job_status

    try:
        # 1. Gather ingredient info and filter out recently-priced ones
        items_to_price = []  # list of {"id": str, "search_term": str}

        async with worker_session() as db:
            for ing_id_str in ingredient_ids:
                ing_id = uuid.UUID(ing_id_str)

                # Check if we have a recent price (< 7 days)
                sm_result = await db.execute(
                    select(StoreMapping).where(StoreMapping.ingredient_id == ing_id)
                )
                existing = sm_result.scalar_one_or_none()

                if existing and existing.updated_at:
                    age = datetime.now(timezone.utc) - existing.updated_at.replace(
                        tzinfo=timezone.utc
                    )
                    if age < timedelta(days=7):
                        continue

                # Find walmart_search_term from recipe ingredient
                ri_result = await db.execute(
                    select(RecipeIngredient)
                    .where(
                        RecipeIngredient.ingredient_id == ing_id,
                        RecipeIngredient.walmart_search_term.isnot(None),
                    )
                    .limit(1)
                )
                ri = ri_result.scalar_one_or_none()

                if ri and ri.walmart_search_term:
                    search_term = ri.walmart_search_term
                else:
                    ing_result = await db.execute(
                        select(Ingredient).where(Ingredient.id == ing_id)
                    )
                    ingredient = ing_result.scalar_one_or_none()
                    if not ingredient:
                        continue
                    search_term = f"{ingredient.name} Great Value"

                items_to_price.append({"id": ing_id_str, "search_term": search_term})

        if not items_to_price:
            async with worker_session() as db:
                await update_job_status(db, uuid.UUID(job_id), "completed", {"updated_count": 0})
            return

        # 2. Single Gemini call for all ingredients
        import json

        gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = (
            "Estimate Walmart prices for these ingredients:\n\n"
            + json.dumps(items_to_price, indent=2)
        )

        gemini_response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_PRICING_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=GeminiPricingOutput,
                temperature=0.2,
            ),
        )

        pricing = GeminiPricingOutput.model_validate_json(gemini_response.text)

        # 3. Save prices to store_mappings
        updated_count = 0
        async with worker_session() as db:
            for item in pricing.prices:
                ing_id = uuid.UUID(item.ingredient_id)

                sm_result = await db.execute(
                    select(StoreMapping).where(StoreMapping.ingredient_id == ing_id)
                )
                existing = sm_result.scalar_one_or_none()

                if existing:
                    existing.last_price = item.estimated_price
                else:
                    db.add(StoreMapping(
                        ingredient_id=ing_id,
                        last_price=item.estimated_price,
                    ))
                updated_count += 1

            await db.commit()

        # 4. Compute cost_per_serving on the recipe
        if recipe_id:
            # Build a price map from what we just saved + existing
            price_map = {uuid.UUID(item.ingredient_id): item.estimated_price for item in pricing.prices}

            async with worker_session() as db:
                # Get all ingredient prices for this recipe
                recipe = await db.get(Recipe, uuid.UUID(recipe_id))
                if recipe:
                    # Fill in any prices we didn't just estimate
                    ri_result = await db.execute(
                        select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe.id)
                    )
                    recipe_ingredients = ri_result.scalars().all()

                    missing_ids = [
                        ri.ingredient_id for ri in recipe_ingredients
                        if ri.ingredient_id not in price_map
                    ]
                    if missing_ids:
                        sm_result = await db.execute(
                            select(StoreMapping).where(StoreMapping.ingredient_id.in_(missing_ids))
                        )
                        for sm in sm_result.scalars().all():
                            if sm.last_price is not None:
                                price_map[sm.ingredient_id] = float(sm.last_price)

                    total_cost = sum(price_map.get(ri.ingredient_id, 0) for ri in recipe_ingredients)
                    if recipe.base_servings and recipe.base_servings > 0:
                        recipe.cost_per_serving = round(total_cost / recipe.base_servings, 2)
                    else:
                        recipe.cost_per_serving = round(total_cost / 4, 2)
                    await db.commit()

        async with worker_session() as db:
            await update_job_status(
                db, uuid.UUID(job_id), "completed", {"updated_count": updated_count}
            )
    except Exception as e:
        async with worker_session() as db:
            from app.services.job_service import update_job_status
            await update_job_status(
                db, uuid.UUID(job_id), "failed", {"error": str(e)}
            )
