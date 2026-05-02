from typing import Any
import httpx
from backend.app.config import settings


class BackboardClient:
    """Minimal Backboard.io client for workflow submission."""

    def __init__(self) -> None:
        if not settings.backboard_api_key:
            raise RuntimeError("BACKBOARD_API_KEY is required to call Backboard.io.")

        self.api_key = settings.backboard_api_key
        self.base_url = settings.backboard_base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def trigger_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Submits a payload to Backboard.io for pipeline execution."""
        workflow_id = settings.backboard_workflow_id
        if not workflow_id:
            raise RuntimeError("BACKBOARD_WORKFLOW_ID is required to launch workflows.")

        endpoint = f"{self.base_url}/workflows/{workflow_id}/runs"
        with httpx.Client(timeout=30.0, headers=self.headers) as client:
            response = client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()

    def submit_story_job(self, story_data: dict[str, Any]) -> dict[str, Any]:
        """Prepare and submit a story job to Backboard."""
        event_payload = {
            "type": "story.create",
            "payload": story_data,
        }
        return self.trigger_workflow(event_payload)
