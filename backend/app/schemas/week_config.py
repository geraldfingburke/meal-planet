import uuid
from datetime import date

from pydantic import BaseModel


class WeekConfigUpdate(BaseModel):
    week_start_date: date
    week_type: str  # "Boy Week" or "Girls Week"


class WeekConfigResponse(BaseModel):
    id: uuid.UUID
    week_start_date: date
    week_type: str
    serving_override: int

    model_config = {"from_attributes": True}
