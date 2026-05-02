from .test import router as test_router
from .story import router as story_router
from .editor import router as editor_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(test_router)
router.include_router(story_router)
router.include_router(editor_router)

__all__ = ['router']