import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.meal_plan import MealPlan
from app.services.ical_service import generate_ical

router = APIRouter()


@router.get("/export.ics")
async def export_calendar(
    start: date,
    end: date,
    db: AsyncSession = Depends(get_db),
):
    if (end - start).days > 365:
        raise HTTPException(status_code=400, detail="Date range too large (max 365 days)")

    stmt = (
        select(MealPlan)
        .options(joinedload(MealPlan.recipe))
        .where(MealPlan.planned_date.between(start, end))
        .order_by(MealPlan.planned_date)
    )
    result = await db.execute(stmt)
    plans = result.scalars().unique().all()

    ical_bytes = generate_ical(list(plans), start, end)

    return Response(
        content=ical_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=meal-plan.ics"},
    )
