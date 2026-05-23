import json
from pathlib import Path
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "NutriMBG API"
    environment: str = "local"
    database_url: str = "postgresql+asyncpg://nutrimbg:nutrimbg@localhost:5432/nutrimbg"
    redis_url: Optional[str] = None
    rate_limit_backend: str = "auto"
    rate_limit_limit: int = 100
    jwt_secret: str = "change-me"
    jwt_exp_hours: int = 8
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"
    recommender_provider: str = "gemini"
    dataset_dir: str = str(ROOT_DIR / "dataset")
    classifier_model_path: str = str(ROOT_DIR / "backend" / "artifacts" / "classifier.joblib")
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:8501",
        "http://localhost:3000",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")


settings = Settings()
