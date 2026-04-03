import uuid
from datetime import datetime

from pydantic import BaseModel, HttpUrl


class RecipeIngredientCreate(BaseModel):
    ingredient_id: uuid.UUID | None = None
    ingredient_name: str | None = None
    quantity: float
    unit: str
    walmart_search_term: str | None = None


class RecipeIngredientResponse(BaseModel):
    ingredient_id: uuid.UUID
    ingredient_name: str
    ingredient_category: str | None = None
    quantity: float
    unit: str
    walmart_search_term: str | None = None

    model_config = {"from_attributes": True}


class RecipeCreate(BaseModel):
    title: str
    instructions: str | None = None
    source_url: str | None = None
    image_url: str | None = None
    base_servings: int = 4
    cost_per_serving: float | None = None
    ingredients: list[RecipeIngredientCreate] = []
    tags: list[str] = []


class RecipeUpdate(BaseModel):
    title: str | None = None
    instructions: str | None = None
    source_url: str | None = None
    image_url: str | None = None
    base_servings: int | None = None
    cost_per_serving: float | None = None
    ingredients: list[RecipeIngredientCreate] | None = None
    tags: list[str] | None = None


class RecipeResponse(BaseModel):
    id: uuid.UUID
    title: str
    instructions: str | None = None
    source_url: str | None = None
    image_url: str | None = None
    base_servings: int
    cost_per_serving: float | None = None
    last_cooked_at: datetime | None = None
    created_at: datetime
    ingredients: list[RecipeIngredientResponse] = []
    tags: list[str] = []

    model_config = {"from_attributes": True}


class RecipeImportRequest(BaseModel):
    url: HttpUrl
