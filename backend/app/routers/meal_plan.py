import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe, Tag
from app.schemas.meal_plan import MealPlanCreate, MealPlanResponse, MealPlanUpdate
from app.services.family_service import get_default_family_id
from app.services.spinner_service import weighted_random_recipe

router = APIRouter()


def _build_response(p: MealPlan) -> MealPlanResponse:
    return MealPlanResponse(
        id=p.id,
        recipe_id=p.recipe_id,
        recipe_title=p.recipe.title,
        planned_date=p.planned_date,
        meal_type=p.meal_type,
        servings=p.servings,
    )


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
    return [_build_response(p) for p in plans]


@router.post("", response_model=MealPlanResponse, status_code=201)
async def create_meal_plan(data: MealPlanCreate, db: AsyncSession = Depends(get_db)):
    family_id = await get_default_family_id(db)
    plan = MealPlan(
        family_id=family_id,
        recipe_id=data.recipe_id,
        planned_date=data.planned_date,
        meal_type=data.meal_type,
        servings=data.servings,
    )
    db.add(plan)
    await db.commit()

    stmt = (
        select(MealPlan)
        .options(joinedload(MealPlan.recipe))
        .where(MealPlan.id == plan.id)
    )
    result = await db.execute(stmt)
    plan = result.scalar_one()
    return _build_response(plan)


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
    if data.servings is not None:
        plan.servings = data.servings

    await db.commit()

    stmt = (
        select(MealPlan)
        .options(joinedload(MealPlan.recipe))
        .where(MealPlan.id == plan.id)
    )
    result = await db.execute(stmt)
    plan = result.scalar_one()
    return _build_response(plan)


@router.delete("/{plan_id}", status_code=204)
async def delete_meal_plan(plan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(MealPlan).where(MealPlan.id == plan_id)
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan entry not found")
    await db.delete(plan)
    await db.commit()


class FillWeekRequest(BaseModel):
    week_start: date
    meal_types: list[str] = ["breakfast", "lunch", "dinner"]
    default_servings: int = 4


@router.post("/fill-week", response_model=list[MealPlanResponse])
async def fill_week(
    data: FillWeekRequest,
    db: AsyncSession = Depends(get_db),
):
    """Auto-fill empty meal slots for the week using category-matched recipes."""
    family_id = await get_default_family_id(db)
    week_end = data.week_start + timedelta(days=6)

    # Load existing plans for the week
    existing_stmt = select(MealPlan).where(
        MealPlan.planned_date.between(data.week_start, week_end)
    )
    existing_result = await db.execute(existing_stmt)
    existing_plans = existing_result.scalars().all()
    filled_slots = {(p.planned_date, p.meal_type) for p in existing_plans}

    # Load all recipes
    all_recipes = (await db.execute(select(Recipe))).scalars().all()
    if not all_recipes:
        raise HTTPException(status_code=400, detail="No recipes available to fill week")

    # Group recipes by category
    category_map: dict[str, list[Recipe]] = {}
    any_recipes: list[Recipe] = []
    for r in all_recipes:
        cat = r.category or "any"
        if cat == "any":
            any_recipes.append(r)
        else:
            category_map.setdefault(cat, []).append(r)

    created = []
    for day_offset in range(7):
        day = data.week_start + timedelta(days=day_offset)
        for meal_type in data.meal_types:
            if (day, meal_type) in filled_slots:
                continue

            # Pick recipes matching the meal_type category, fall back to "any"
            candidates = category_map.get(meal_type, []) + any_recipes
            if not candidates:
                candidates = list(all_recipes)

            selected = weighted_random_recipe(candidates)

            plan = MealPlan(
                family_id=family_id,
                recipe_id=selected.id,
                planned_date=day,
                meal_type=meal_type,
                servings=data.default_servings,
            )
            db.add(plan)
            created.append(plan)

    await db.commit()

    # Reload with recipe relationships
    if not created:
        return []

    plan_ids = [p.id for p in created]
    stmt = (
        select(MealPlan)
        .options(joinedload(MealPlan.recipe))
        .where(MealPlan.id.in_(plan_ids))
        .order_by(MealPlan.planned_date, MealPlan.meal_type)
    )
    result = await db.execute(stmt)
    plans = result.scalars().unique().all()
    return [_build_response(p) for p in plans]
