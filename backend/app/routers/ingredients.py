from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ingredient import Ingredient
from app.schemas.ingredient import IngredientCreate, IngredientResponse

router = APIRouter()


@router.get("", response_model=list[IngredientResponse])
async def list_ingredients(
    q: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Ingredient).order_by(Ingredient.name)
    if q:
        stmt = stmt.where(Ingredient.name.ilike(f"%{q}%"))
    if category:
        stmt = stmt.where(Ingredient.category == category)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=IngredientResponse, status_code=201)
async def create_ingredient(
    data: IngredientCreate, db: AsyncSession = Depends(get_db)
):
    ingredient = Ingredient(name=data.name, category=data.category)
    db.add(ingredient)
    await db.commit()
    await db.refresh(ingredient)
    return ingredient
