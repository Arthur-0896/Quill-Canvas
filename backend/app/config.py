from pathlib import Path
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    
    # Quill Canvas settings
    backboard_api_key: str | None = None
    backboard_assistant_id: str | None = None
    backboard_workflow_id: str | None = None
    backboard_base_url: str = "https://api.backboard.io"
    
    # API settings
    api_title: str = "Quill Canvas Storybook Backend"
    api_version: str = "0.1.0"
    api_description: str = "Backend scaffold for story scene extraction, AI image orchestration, and Backboard.io workflow execution."
    
    # CORS origins
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = Path.cwd() / ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# For backward compatibility
ENVIRONMENT = settings.environment
IS_PRODUCTION = ENVIRONMENT == "production"
API_TITLE = settings.api_title
API_VERSION = settings.api_version
API_DESCRIPTION = settings.api_description
CORS_ORIGINS = settings.cors_origins
