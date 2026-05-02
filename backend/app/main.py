from fastapi import FastAPI
from backend.app.api.v1.endpoints import router as api_router
from backend.app.config import settings

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
)

app.include_router(api_router)


@app.get("/api/health")
def health_check() -> dict:
    """Health endpoint for readiness checks."""
    return {
        "status": "ok",
        "environment": settings.environment,
        "backboard_enabled": settings.backboard_api_key is not None,
    }
