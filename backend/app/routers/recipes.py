import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe, RecipeIngredient, RecipeTag, Tag
from app.schemas.recipe import (
    RecipeCreate,
    RecipeImportRequest,
    RecipeResponse,
    RecipeUpdate,
)
from app.services.recipe_service import build_recipe_response, upsert_recipe_ingredients

router = APIRouter()


@router.get("", response_model=list[RecipeResponse])
async def list_recipes(
    tag: str | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Recipe)
        .options(selectinload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))
        .options(selectinload(Recipe.tags))
        .order_by(Recipe.created_at.desc())
    )
    if q:
        stmt = stmt.where(Recipe.title.ilike(f"%{q}%"))
    if tag:
        stmt = stmt.join(Recipe.tags).where(Tag.name == tag)

    result = await db.execute(stmt)
    recipes = result.scalars().unique().all()
    return [build_recipe_response(r) for r in recipes]


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(recipe_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(selectinload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))
        .options(selectinload(Recipe.tags))
    )
    result = await db.execute(stmt)
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return build_recipe_response(recipe)


@router.post("", response_model=RecipeResponse, status_code=201)
async def create_recipe(data: RecipeCreate, db: AsyncSession = Depends(get_db)):
    # Get or create the default family
    from app.services.family_service import get_default_family_id

    family_id = await get_default_family_id(db)

    recipe = Recipe(
        family_id=family_id,
        title=data.title,
        instructions=data.instructions,
        source_url=data.source_url,
        base_servings=data.base_servings,
    )
    db.add(recipe)
    await db.flush()

    await upsert_recipe_ingredients(db, recipe.id, data.ingredients)
    await _sync_tags(db, recipe, data.tags)

    await db.commit()

    # Reload with relationships
    return await get_recipe(recipe.id, db)


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: uuid.UUID,
    data: RecipeUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Recipe).where(Recipe.id == recipe_id)
    result = await db.execute(stmt)
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if data.title is not None:
        recipe.title = data.title
    if data.instructions is not None:
        recipe.instructions = data.instructions
    if data.source_url is not None:
        recipe.source_url = data.source_url
    if data.base_servings is not None:
        recipe.base_servings = data.base_servings

    if data.ingredients is not None:
        await upsert_recipe_ingredients(db, recipe.id, data.ingredients)
    if data.tags is not None:
        await _sync_tags(db, recipe, data.tags)

    await db.commit()
    return await get_recipe(recipe.id, db)


@router.delete("/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Recipe).where(Recipe.id == recipe_id)
    result = await db.execute(stmt)
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    await db.delete(recipe)
    await db.commit()


@router.post("/import", status_code=202)
async def import_recipe(data: RecipeImportRequest, db: AsyncSession = Depends(get_db)):
    from app.services.job_service import create_job
    from app.tasks.parse_recipe import parse_recipe_task

    job = await create_job(db, "recipe_import", {"url": str(data.url)})
    parse_recipe_task.send(str(job.id), str(data.url))
    return {"job_id": str(job.id), "status": "pending"}


async def _sync_tags(db: AsyncSession, recipe: Recipe, tag_names: list[str]):
    """Replace recipe's tags with the given tag names, creating new tags as needed."""
    # Clear existing tags
    await db.execute(
        RecipeTag.__table__.delete().where(RecipeTag.recipe_id == recipe.id)
    )

    for name in tag_names:
        name = name.strip().lower()
        if not name:
            continue
        # Get or create tag
        result = await db.execute(select(Tag).where(Tag.name == name))
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            await db.flush()
        db.add(RecipeTag(recipe_id=recipe.id, tag_id=tag.id))
