from fastapi import APIRouter, HTTPException
from backend.app.schemas import StoryRequest, StoryPreviewResponse, BackboardLaunchResponse
from backend.app.services.story_processor import extract_scenes, build_backboard_payload
from backend.app.backboard import BackboardClient
from backend.app.config import settings

router = APIRouter(prefix="/api/story", tags=["story"])


@router.post("/preview", response_model=StoryPreviewResponse)
async def preview_story(story: StoryRequest) -> StoryPreviewResponse:
    """Returns a preview of extracted scenes from the submitted story text."""
    try:
        scenes = extract_scenes(story)
        return StoryPreviewResponse(
            story_title=story.title,
            scene_count=len(scenes),
            scenes=scenes,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/launch", response_model=BackboardLaunchResponse)
async def launch_story_workflow(story: StoryRequest) -> BackboardLaunchResponse:
    """Launches the Backboard.io workflow to process the story end-to-end."""
    try:
        if not settings.backboard_api_key or not settings.backboard_workflow_id:
            raise HTTPException(
                status_code=500,
                detail="Backboard integration is not configured. Set BACKBOARD_API_KEY and BACKBOARD_WORKFLOW_ID.",
            )

        scenes = extract_scenes(story)
        payload = build_backboard_payload(story, scenes)
        client = BackboardClient()
        response = client.submit_story_job(payload)

        run_id = response.get("run_id") or response.get("id") or "unknown"
        return BackboardLaunchResponse(
            job_id=str(run_id),
            workflow_id=settings.backboard_workflow_id,
            status="started",
            message="Backboard workflow launched successfully.",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
