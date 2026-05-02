import asyncio
import json
import uuid
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from backend.app.services.story_processor import extract_scenes
from backend.app.services.ai.bedrock_generator import AWSBedrockImageGenerator
from backend.app.schemas import StoryRequest, SceneSummary


class ConnectionManager:
    """Manage WebSocket connections and broadcast scene updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.image_generator = AWSBedrockImageGenerator()
        self.processing_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self, story_id: str, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[story_id] = websocket
        print(f"Client {story_id} connected")
    
    async def disconnect(self, story_id: str):
        """Remove disconnected client"""
        if story_id in self.active_connections:
            del self.active_connections[story_id]
        
        # Cancel any pending tasks for this story
        if story_id in self.processing_tasks:
            self.processing_tasks[story_id].cancel()
            del self.processing_tasks[story_id]
        
        print(f"Client {story_id} disconnected")
    
    async def send_personal(self, story_id: str, data: dict):
        """Send message to specific client"""
        if story_id in self.active_connections:
            await self.active_connections[story_id].send_json(data)
    
    async def broadcast(self, message: dict):
        """Broadcast to all connected clients"""
        for connection in self.active_connections.values():
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Broadcast error: {e}")
    
    async def process_story_realtime(self, story_id: str, story_data: StoryRequest):
        """
        Process story in real-time:
        1. Extract scenes
        2. Generate image prompts
        3. Stream to frontend
        """
        try:
            # Send processing started signal
            await self.send_personal(story_id, {
                "type": "processing_started",
                "message": "Analyzing story and detecting scenes..."
            })
            
            # Extract scenes from story
            scenes = extract_scenes(story_data)
            
            # Process each scene
            for idx, scene in enumerate(scenes):
                # Create image prompt
                image_prompt = self._create_image_prompt(scene)
                
                # Send scene detected
                await self.send_personal(story_id, {
                    "type": "scene_detected",
                    "scene_id": scene.scene_id,
                    "sequence": idx + 1,
                    "title": scene.title,
                    "description": scene.description,
                    "image_prompt": image_prompt
                })
                
                # Send image generation started
                await self.send_personal(story_id, {
                    "type": "image_generating",
                    "scene_id": scene.scene_id,
                    "message": f"Generating image for: {scene.title}..."
                })
                
                # Generate image using AWS Bedrock
                try:
                    image_base64 = await self.image_generator.generate_image(image_prompt)
                    
                    # Send generated image to frontend
                    await self.send_personal(story_id, {
                        "type": "image_generated",
                        "scene_id": scene.scene_id,
                        "image_base64": image_base64,  # Send as data URL
                        "image_prompt": image_prompt
                    })
                    
                except Exception as e:
                    await self.send_personal(story_id, {
                        "type": "image_error",
                        "scene_id": scene.scene_id,
                        "error": str(e)
                    })
                
                # Small delay between generations
                await asyncio.sleep(1)
            
            # Send completion signal
            await self.send_personal(story_id, {
                "type": "processing_completed",
                "total_scenes": len(scenes),
                "message": "Story processing completed!"
            })
            
        except Exception as e:
            await self.send_personal(story_id, {
                "type": "error",
                "error": str(e)
            })
    
    def _create_image_prompt(self, scene: SceneSummary) -> str:
        """Create detailed image prompt from scene description"""
        return f"""
        Create a vivid, cinematic illustration for this scene:
        Title: {scene.title}
        Description: {scene.description}
        
        Style: illustrated, storybook art, vibrant colors, detailed
        Aspect ratio: 3:4 portrait
        """


# Global connection manager
manager = ConnectionManager()
