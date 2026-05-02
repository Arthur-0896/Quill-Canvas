from pydantic import BaseModel, Field
from typing import List


class StoryRequest(BaseModel):
    title: str = Field(..., example="The Lost Library")
    author: str | None = Field(None, example="Avery")
    text: str = Field(..., example="Once upon a time, a child discovered a secret library...")


class SceneSummary(BaseModel):
    scene_id: int
    title: str
    description: str
    prompt_hint: str


class StoryPreviewResponse(BaseModel):
    story_title: str
    scene_count: int
    scenes: List[SceneSummary]


class BackboardLaunchResponse(BaseModel):
    job_id: str
    workflow_id: str
    status: str
    message: str
