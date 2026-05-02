from pathlib import Path
from pydantic import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    backboard_api_key: str | None = None
    backboard_workflow_id: str | None = None
    backboard_base_url: str = "https://api.backboard.io"

    class Config:
        env_file = Path.cwd() / ".env"
        env_file_encoding = "utf-8"


settings = Settings()
