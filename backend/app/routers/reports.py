import json
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.grocery_archive import GroceryListArchive
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe

router = APIRouter()


@router.get("/spending-over-time")
async def spending_over_time(db: AsyncSession = Depends(get_db)):
    """Return grocery list totals over time for charting."""
    stmt = (
        select(
            GroceryListArchive.start_date,
            GroceryListArchive.end_date,
            GroceryListArchive.estimated_total,
            GroceryListArchive.created_at,
        )
        .order_by(GroceryListArchive.created_at.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            "estimated_total": float(r.estimated_total),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/top-recipes")
async def top_recipes(limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Return the most frequently used recipes in meal plans."""
    stmt = (
        select(
            MealPlan.recipe_id,
            Recipe.title,
            func.count(MealPlan.id).label("usage_count"),
        )
        .join(Recipe, MealPlan.recipe_id == Recipe.id)
        .group_by(MealPlan.recipe_id, Recipe.title)
        .order_by(func.count(MealPlan.id).desc())
        .limit(min(limit, 20))
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "recipe_id": str(r.recipe_id),
            "title": r.title,
            "usage_count": r.usage_count,
        }
        for r in rows
    ]


@router.get("/most-expensive-day")
async def most_expensive_day(db: AsyncSession = Depends(get_db)):
    """Return the most expensive planned day based on recipe cost_per_serving * servings."""
    stmt = (
        select(
            MealPlan.planned_date,
            func.sum(Recipe.cost_per_serving * MealPlan.servings).label("total_cost"),
        )
        .join(Recipe, MealPlan.recipe_id == Recipe.id)
        .where(Recipe.cost_per_serving.isnot(None))
        .group_by(MealPlan.planned_date)
        .order_by(func.sum(Recipe.cost_per_serving * MealPlan.servings).desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        return {"date": None, "total_cost": 0}
    return {
        "date": row.planned_date.isoformat(),
        "total_cost": round(float(row.total_cost), 2),
    }


@router.get("/avg-spending-by-category")
async def avg_spending_by_category(db: AsyncSession = Depends(get_db)):
    """Average grocery spending by store aisle category across all archived lists."""
    stmt = select(GroceryListArchive.items_json).order_by(
        GroceryListArchive.created_at.desc()
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    category_totals: dict[str, list[float]] = {}
    for items_json in rows:
        items = json.loads(items_json)
        for item in items:
            cat = item.get("category", "Other")
            category_totals.setdefault(cat, []).append(item.get("estimated_price", 0))

    return [
        {
            "category": cat,
            "avg_spending": round(sum(prices) / max(len(rows), 1), 2),
            "total_spending": round(sum(prices), 2),
            "list_count": len(rows),
        }
        for cat, prices in sorted(category_totals.items())
    ]
