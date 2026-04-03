import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.family import Family

_default_family_id: uuid.UUID | None = None


async def get_default_family_id(db: AsyncSession) -> uuid.UUID:
    global _default_family_id
    if _default_family_id:
        return _default_family_id

    result = await db.execute(select(Family).limit(1))
    family = result.scalar_one_or_none()

    if not family:
        family = Family(name="My Family")
        db.add(family)
        await db.flush()

    _default_family_id = family.id
    return family.id
