from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://mealplanet:mealplanet_dev@db:5432/mealplanet"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    # Gemini
    GEMINI_API_KEY: str = ""

    # App
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
