from app.routers.grocery import router as grocery_router
from app.routers.ingredients import router as ingredients_router
from app.routers.meal_plan import router as meal_plan_router
from app.routers.recipes import router as recipes_router
from app.routers.spinner import router as spinner_router
from app.routers.week_config import router as week_config_router

__all__ = [
    "recipes_router",
    "ingredients_router",
    "meal_plan_router",
    "week_config_router",
    "grocery_router",
    "spinner_router",
]
