from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://jobscore:jobscore@localhost:5432/jobscore"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str = "change-me"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    MATCH_SCORE_THRESHOLD: float = 0.35
    REQUIRED_SKILL_WEIGHT: float = 0.75
    PREFERRED_SKILL_WEIGHT: float = 0.25
    DAILY_SWIPE_CAP: int = 50
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
