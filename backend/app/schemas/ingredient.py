import uuid

from pydantic import BaseModel


class IngredientCreate(BaseModel):
    name: str
    category: str | None = None


class IngredientResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: str | None = None

    model_config = {"from_attributes": True}
