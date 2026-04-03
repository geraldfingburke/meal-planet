import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.meal_plan import MealPlan
from app.schemas.meal_plan import MealPlanCreate, MealPlanResponse, MealPlanUpdate
from app.services.family_service import get_default_family_id

router = APIRouter()


@router.get("", response_model=list[MealPlanResponse])
async def list_meal_plan(
    week_start: date,
    db: AsyncSession = Depends(get_db),
):
    week_end = week_start + timedelta(days=6)
    stmt = (
        select(MealPlan)
        .options(joinedload(MealPlan.recipe))
        .where(MealPlan.planned_date.between(week_start, week_end))
        .order_by(MealPlan.planned_date, MealPlan.meal_type)
    )
    result = await db.execute(stmt)
    plans = result.scalars().unique().all()
    return [
        MealPlanResponse(
            id=p.id,
            recipe_id=p.recipe_id,
            recipe_title=p.recipe.title,
            planned_date=p.planned_date,
            meal_type=p.meal_type,
        )
        for p in plans
    ]


@router.post("", response_model=MealPlanResponse, status_code=201)
async def create_meal_plan(data: MealPlanCreate, db: AsyncSession = Depends(get_db)):
    family_id = await get_default_family_id(db)
    plan = MealPlan(
        family_id=family_id,
        recipe_id=data.recipe_id,
        planned_date=data.planned_date,
        meal_type=data.meal_type,
    )
    db.add(plan)
    await db.commit()

    # Reload with recipe
    stmt = (
        select(MealPlan)
        .options(joinedload(MealPlan.recipe))
        .where(MealPlan.id == plan.id)
    )
    result = await db.execute(stmt)
    plan = result.scalar_one()
    return MealPlanResponse(
        id=plan.id,
        recipe_id=plan.recipe_id,
        recipe_title=plan.recipe.title,
        planned_date=plan.planned_date,
        meal_type=plan.meal_type,
    )


@router.put("/{plan_id}", response_model=MealPlanResponse)
async def update_meal_plan(
    plan_id: uuid.UUID,
    data: MealPlanUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MealPlan).where(MealPlan.id == plan_id)
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan entry not found")

    if data.recipe_id is not None:
        plan.recipe_id = data.recipe_id
    if data.planned_date is not None:
        plan.planned_date = data.planned_date
    if data.meal_type is not None:
        plan.meal_type = data.meal_type

    await db.commit()

    # Reload with recipe
    stmt = (
        select(MealPlan)
        .options(joinedload(MealPlan.recipe))
        .where(MealPlan.id == plan.id)
    )
    result = await db.execute(stmt)
    plan = result.scalar_one()
    return MealPlanResponse(
        id=plan.id,
        recipe_id=plan.recipe_id,
        recipe_title=plan.recipe.title,
        planned_date=plan.planned_date,
        meal_type=plan.meal_type,
    )


@router.delete("/{plan_id}", status_code=204)
async def delete_meal_plan(plan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(MealPlan).where(MealPlan.id == plan_id)
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan entry not found")
    await db.delete(plan)
    await db.commit()
