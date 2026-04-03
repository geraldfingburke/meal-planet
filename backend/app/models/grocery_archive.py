import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.family import Base


class GroceryListArchive(Base):
    __tablename__ = "grocery_list_archives"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("families.id"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    items_json: Mapped[str] = mapped_column(Text, nullable=False)
    recipes_json: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    recipe_cost_total: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
