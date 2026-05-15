from pathlib import Path
from typing import Optional

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
    dataset_dir: str = str(ROOT_DIR / "dataset")
    classifier_model_path: str = str(ROOT_DIR / "backend" / "artifacts" / "classifier.joblib")

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")


settings = Settings()
