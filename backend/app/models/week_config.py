import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.family import Base


class WeekConfig(Base):
    __tablename__ = "week_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("families.id"), nullable=False
    )
    week_start_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    week_type: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("week_type IN ('Boy Week', 'Girls Week')"),
        nullable=False,
    )
    serving_override: Mapped[int] = mapped_column(Integer, nullable=False)
