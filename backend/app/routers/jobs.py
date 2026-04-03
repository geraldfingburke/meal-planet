import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job_queue import JobQueue

router = APIRouter()


@router.get("/{job_id}")
async def get_job_status(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(JobQueue).where(JobQueue.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    import json

    return {
        "id": str(job.id),
        "job_type": job.job_type,
        "status": job.status,
        "result": json.loads(job.result) if job.result else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }
