import uuid
from datetime import date

from pydantic import BaseModel


class MealPlanCreate(BaseModel):
    recipe_id: uuid.UUID
    planned_date: date
    meal_type: str | None = None


class MealPlanUpdate(BaseModel):
    recipe_id: uuid.UUID | None = None
    planned_date: date | None = None
    meal_type: str | None = None


class MealPlanResponse(BaseModel):
    id: uuid.UUID
    recipe_id: uuid.UUID
    recipe_title: str
    planned_date: date
    meal_type: str | None = None

    model_config = {"from_attributes": True}
