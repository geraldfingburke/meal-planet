from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.week_config import WeekConfig
from app.schemas.week_config import WeekConfigResponse, WeekConfigUpdate
from app.services.family_service import get_default_family_id

router = APIRouter()

WEEK_TYPE_SERVINGS = {"Boy Week": 4, "Girls Week": 6}


@router.get("", response_model=WeekConfigResponse | None)
async def get_week_config(
    week_start: date,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WeekConfig).where(WeekConfig.week_start_date == week_start)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    if not config:
        return None
    return config


@router.put("", response_model=WeekConfigResponse)
async def set_week_config(
    data: WeekConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    if data.week_type not in WEEK_TYPE_SERVINGS:
        raise HTTPException(
            status_code=400,
            detail=f"week_type must be one of: {list(WEEK_TYPE_SERVINGS.keys())}",
        )

    family_id = await get_default_family_id(db)
    serving_override = WEEK_TYPE_SERVINGS[data.week_type]

    stmt = select(WeekConfig).where(
        WeekConfig.week_start_date == data.week_start_date
    )
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if config:
        config.week_type = data.week_type
        config.serving_override = serving_override
    else:
        config = WeekConfig(
            family_id=family_id,
            week_start_date=data.week_start_date,
            week_type=data.week_type,
            serving_override=serving_override,
        )
        db.add(config)

    await db.commit()
    await db.refresh(config)
    return config
