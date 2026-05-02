from fastapi import FastAPI
from app.api.v1.endpoints import router
from app.core import config
from app.core.logging import setup_logging, get_logger

app = FastAPI(
    title=config.API_TITLE,
    description=config.API_DESCRIPTION,
    version=config.API_VERSION
)

app.include_router(router)

setup_logging()
logger = get_logger(__name__)

@app.get("/")
def read_root():
    return {"Hello": "World"}
