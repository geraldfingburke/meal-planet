from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    grocery,
    ingredients,
    meal_plan,
    recipes,
    spinner,
)
from app.routers import calendar as calendar_router
from app.routers import jobs as jobs_router
from app.routers import reports as reports_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they don't exist (bootstraps fresh DB)
    from app.database import engine
    from app.models.family import Base
    import app.models  # noqa: F401 — registers all models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add columns that create_all won't add to existing tables
        await conn.execute(
            __import__("sqlalchemy").text(
                "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS image_url TEXT"
            )
        )
        await conn.execute(
            __import__("sqlalchemy").text(
                "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS cost_per_serving NUMERIC(10,2)"
            )
        )
        await conn.execute(
            __import__("sqlalchemy").text(
                "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS category VARCHAR(20) DEFAULT 'any' NOT NULL"
            )
        )
        await conn.execute(
            __import__("sqlalchemy").text(
                "ALTER TABLE meal_plan ADD COLUMN IF NOT EXISTS servings INTEGER DEFAULT 4 NOT NULL"
            )
        )
        # Fix FK constraints to cascade on delete
        await conn.execute(
            __import__("sqlalchemy").text(
                "ALTER TABLE meal_plan DROP CONSTRAINT IF EXISTS meal_plan_recipe_id_fkey"
            )
        )
        await conn.execute(
            __import__("sqlalchemy").text(
                "ALTER TABLE meal_plan ADD CONSTRAINT meal_plan_recipe_id_fkey"
                " FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE"
            )
        )
    yield


app = FastAPI(
    title="Meal Planet API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ──────────────────────────────────────────
app.include_router(recipes.router, prefix="/api/recipes", tags=["recipes"])
app.include_router(ingredients.router, prefix="/api/ingredients", tags=["ingredients"])
app.include_router(meal_plan.router, prefix="/api/meal-plan", tags=["meal-plan"])
app.include_router(grocery.router, prefix="/api/grocery-list", tags=["grocery"])
app.include_router(spinner.router, prefix="/api/spinner", tags=["spinner"])
app.include_router(calendar_router.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(jobs_router.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(reports_router.router, prefix="/api/reports", tags=["reports"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
