from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.recipe import Recipe, Tag
from app.schemas.recipe import RecipeResponse
from app.services.recipe_service import build_recipe_response
from app.services.spinner_service import weighted_random_recipe

router = APIRouter()


@router.get("/spin")
async def spin(
    tags: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Recipe)

    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
        if tag_list:
            stmt = stmt.join(Recipe.tags).where(Tag.name.in_(tag_list))

    result = await db.execute(stmt)
    recipes = result.scalars().unique().all()

    if not recipes:
        return {"recipe": None, "message": "No recipes match the given filters."}

    selected = weighted_random_recipe(list(recipes))

    # Reload full recipe with relationships for response
    from app.routers.recipes import get_recipe

    recipe_response = await get_recipe(selected.id, db)
    return {"recipe": recipe_response}


@router.get("/tags", response_model=list[str])
async def list_tags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag.name).order_by(Tag.name))
    return result.scalars().all()
