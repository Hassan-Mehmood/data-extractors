from functools import lru_cache
from typing import Optional

# from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: Optional[str] = None
    EXPORTS_DIR: str = "exports"


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()  # type: ignore
    return settings
