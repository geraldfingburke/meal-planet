import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_queue import JobQueue


async def create_job(db: AsyncSession, job_type: str, payload: dict) -> JobQueue:
    job = JobQueue(
        job_type=job_type,
        status="pending",
        payload=json.dumps(payload),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def update_job_status(
    db: AsyncSession, job_id: uuid.UUID, status: str, result: dict | None = None
):
    from sqlalchemy import select

    stmt = select(JobQueue).where(JobQueue.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if job:
        job.status = status
        if result:
            job.result = json.dumps(result)
        await db.commit()
