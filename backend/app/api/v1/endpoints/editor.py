from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from backend.app.services.websocket_manager import manager
from backend.app.schemas import StoryRequest
import uuid

router = APIRouter(prefix="/api/editor", tags=["editor"])


@router.websocket("/ws/{story_id}")
async def websocket_editor(websocket: WebSocket, story_id: str):
    """
    WebSocket endpoint for real-time story editing and image generation.
    
    Client sends:
    - {"type": "story_update", "content": "..."}
    
    Server sends:
    - {"type": "scene_detected", "scene_id": "...", "title": "...", ...}
    - {"type": "image_generating", "scene_id": "...", ...}
    - {"type": "image_generated", "scene_id": "...", "image_base64": "...", ...}
    - {"type": "processing_completed", ...}
    - {"type": "error", "error": "..."}
    """
    await manager.connect(story_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "story_update":
                # User typed new content
                story_content = data.get("content", "")
                
                # Create story request from incoming data
                story_request = StoryRequest(
                    title=data.get("title", "Untitled Story"),
                    author=data.get("author"),
                    text=story_content
                )
                
                # Process story in real-time
                await manager.process_story_realtime(story_id, story_request)
            
            elif data.get("type") == "ping":
                # Keep-alive ping/pong
                await manager.send_personal(story_id, {"type": "pong"})
    
    except WebSocketDisconnect:
        await manager.disconnect(story_id)
    except Exception as e:
        await manager.send_personal(story_id, {
            "type": "error",
            "error": str(e)
        })
        await manager.disconnect(story_id)
