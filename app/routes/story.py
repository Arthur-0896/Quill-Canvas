from fastapi import APIRouter, HTTPException
from app.schemas import StoryRequest, StoryPreviewResponse, BackboardLaunchResponse
from app.services.story_processor import extract_scenes, build_backboard_payload
from app.backboard import BackboardClient
from app.config import settings

router = APIRouter()


@router.post("/story/preview", response_model=StoryPreviewResponse)
def preview_story(story: StoryRequest) -> StoryPreviewResponse:
    """Returns a preview of extracted scenes from the submitted story text."""
    scenes = extract_scenes(story)
    return StoryPreviewResponse(
        story_title=story.title,
        scene_count=len(scenes),
        scenes=scenes,
    )


@router.post("/story/launch", response_model=BackboardLaunchResponse)
def launch_story_workflow(story: StoryRequest) -> BackboardLaunchResponse:
    """Launches the Backboard.io workflow to process the story end-to-end."""
    if not settings.backboard_api_key or not settings.backboard_workflow_id:
        raise HTTPException(
            status_code=500,
            detail="Backboard integration is not configured. Set BACKBOARD_API_KEY and BACKBOARD_WORKFLOW_ID.",
        )

    scenes = extract_scenes(story)
    payload = build_backboard_payload(story, scenes)

    try:
        client = BackboardClient()
        response = client.submit_story_job(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    run_id = response.get("run_id") or response.get("id") or "unknown"
    return BackboardLaunchResponse(
        job_id=str(run_id),
        workflow_id=settings.backboard_workflow_id,
        status="started",
        message="Backboard workflow launched successfully.",
    )
