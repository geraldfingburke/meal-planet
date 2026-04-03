from app.routers.grocery import router as grocery_router
from app.routers.ingredients import router as ingredients_router
from app.routers.meal_plan import router as meal_plan_router
from app.routers.recipes import router as recipes_router
from app.routers.reports import router as reports_router
from app.routers.spinner import router as spinner_router

__all__ = [
    "recipes_router",
    "ingredients_router",
    "meal_plan_router",
    "grocery_router",
    "spinner_router",
    "reports_router",
]
