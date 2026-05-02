from backend.app.schemas import StoryRequest, SceneSummary


def extract_scenes(story: StoryRequest) -> list[SceneSummary]:
    """Stub for scene extraction logic.

    Replace this with your AI scene analysis implementation.
    """
    paragraphs = [p.strip() for p in story.text.split("\n\n") if p.strip()]
    scenes: list[SceneSummary] = []
    for idx, paragraph in enumerate(paragraphs, start=1):
        scenes.append(
            SceneSummary(
                scene_id=idx,
                title=f"Scene {idx}",
                description=paragraph[:120] + ("..." if len(paragraph) > 120 else ""),
                prompt_hint=f"Illustrate a vivid scene about: {paragraph[:80]}",
            )
        )
    return scenes


def build_backboard_payload(story: StoryRequest, scenes: list[SceneSummary]) -> dict:
    """Build the structured payload that Backboard.io can consume."""
    return {
        "story": {
            "title": story.title,
            "author": story.author,
            "text": story.text,
        },
        "scenes": [scene.dict() for scene in scenes],
        "meta": {
            "source": "quill-canvas-fastapi",
        },
    }
