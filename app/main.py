from fastapi import FastAPI
from app.routes.story import router as story_router
from app.config import settings

app = FastAPI(
    title="Quill Canvas Storybook Backend",
    description="Backend scaffold for story scene extraction, AI image orchestration, and Backboard.io workflow execution.",
    version="0.1.0",
)

app.include_router(story_router, prefix="/api")


@app.get("/api/health")
def health_check() -> dict:
    """Health endpoint for readiness checks."""
    return {
        "status": "ok",
        "environment": settings.environment,
        "backboard_enabled": settings.backboard_api_key is not None,
    }
