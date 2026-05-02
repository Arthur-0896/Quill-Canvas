from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import time
import os
import logging

# ---------------- LOGGING SETUP ----------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- BACKBOARD CONFIG ----------------
BACKBOARD_URL = "https://app.backboard.io/api"
ASSISTANT_ID = "9b6415dc-79dd-468f-8399-4fb57306be4e"
API_KEY = "espr_8oGMKow5gEEFba8V7KpaR7Zh651S78qZq8RvILvRmQc"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# ---------------- LEONARDO CONFIG ----------------
LEONARDO_API_KEY = "32f89283-536d-4deb-bf84-86252952a29b"

LEO_BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"

LEO_HEADERS = {
    "Authorization": f"Bearer {LEONARDO_API_KEY}",
    "Content-Type": "application/json"
}

# ---------------- REQUEST MODEL ----------------
class StoryRequest(BaseModel):
    story: str


# ---------------- BACKBOARD CALL ----------------
def generate_prompt_with_backboard(story: str, max_retries: int = 3) -> str:
    """
    Generate a prompt using Backboard AI assistant.
    
    Args:
        story: The story text to send to Backboard
        max_retries: Maximum number of retry attempts
        
    Returns:
        Generated prompt string
        
    Raises:
        HTTPException: If the API call fails after retries
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"[Backboard] Attempt {attempt + 1}/{max_retries}: Sending story ({len(story)} chars)")
            
            response = requests.post(
                f"{BACKBOARD_URL}/threads/messages",
                headers=HEADERS,
                json={
                    "content": story,
                    "assistant_id": ASSISTANT_ID
                },
                timeout=30
            )
            
            # Log response status
            logger.info(f"[Backboard] Response status: {response.status_code}")
            
            # Check for rate limiting
            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", 60))
                logger.warning(f"[Backboard] Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            # Raise for bad status codes
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"[Backboard] Response data: {data}")
            
            # Extract prompt from response
            prompt = data.get("content") or data.get("response") or data.get("message")
            
            if not prompt:
                logger.error(f"[Backboard] No prompt in response: {data}")
                raise ValueError(f"Invalid response format from Backboard: {data}")
            
            logger.info(f"[Backboard] Successfully generated prompt ({len(prompt)} chars)")
            return prompt
            
        except requests.exceptions.Timeout:
            logger.error(f"[Backboard] Request timeout on attempt {attempt + 1}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=504, detail="Backboard API timeout")
            time.sleep(2 ** attempt)  # Exponential backoff
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[Backboard] Request error: {str(e)}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=502, detail=f"Backboard API error: {str(e)}")
            time.sleep(2 ** attempt)
            
        except ValueError as e:
            logger.error(f"[Backboard] Value error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    raise HTTPException(status_code=500, detail="Failed to generate prompt after all retries")


# ---------------- LEONARDO ----------------
def create_generation(prompt: str, max_retries: int = 3) -> str:
    """
    Create an image generation job with Leonardo AI.
    
    Args:
        prompt: The text prompt for image generation
        max_retries: Maximum number of retry attempts
        
    Returns:
        Generation ID string
        
    Raises:
        HTTPException: If the API call fails after retries
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"[Leonardo] Attempt {attempt + 1}/{max_retries}: Creating generation")
            
            payload = {
                "prompt": f"{prompt}, black and white pencil sketch, cinematic lighting, highly detailed",
                "modelId": "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3",
                "num_images": 1,
                "width": 1024,
                "height": 1024
            }
            
            res = requests.post(
                f"{LEO_BASE_URL}/generations",
                headers=LEO_HEADERS,
                json=payload,
                timeout=30
            )
            
            logger.info(f"[Leonardo] Create response status: {res.status_code}")
            
            # Handle rate limiting
            if res.status_code == 429:
                wait_time = int(res.headers.get("Retry-After", 60))
                logger.warning(f"[Leonardo] Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            # Check for other errors
            if res.status_code != 200:
                logger.error(f"[Leonardo] Error response: {res.text}")
                if attempt == max_retries - 1:
                    raise HTTPException(status_code=res.status_code, detail=f"Leonardo API error: {res.text}")
                time.sleep(2 ** attempt)
                continue
            
            data = res.json()
            logger.debug(f"[Leonardo] Response data: {data}")
            
            generation_id = data.get("sdGenerationJob", {}).get("generationId")
            
            if not generation_id:
                logger.error(f"[Leonardo] No generation ID in response: {data}")
                raise ValueError(f"Invalid response from Leonardo: {data}")
            
            logger.info(f"[Leonardo] Generation created: {generation_id}")
            return generation_id
            
        except requests.exceptions.Timeout:
            logger.error(f"[Leonardo] Request timeout on attempt {attempt + 1}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=504, detail="Leonardo API timeout")
            time.sleep(2 ** attempt)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[Leonardo] Request error: {str(e)}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=502, detail=f"Leonardo API error: {str(e)}")
            time.sleep(2 ** attempt)
    
    raise HTTPException(status_code=500, detail="Failed to create generation after all retries")


def wait_for_image(gen_id: str, timeout: int = 300, poll_interval: int = 3) -> str:
    """
    Poll Leonardo API until image generation is complete.
    
    Args:
        gen_id: Generation ID to poll
        timeout: Maximum time to wait in seconds (default 5 minutes)
        poll_interval: Time between polls in seconds
        
    Returns:
        URL of the generated image
        
    Raises:
        HTTPException: If generation fails or times out
    """
    start_time = time.time()
    attempt = 0
    
    logger.info(f"[Leonardo] Waiting for image generation: {gen_id}")
    
    while True:
        attempt += 1
        elapsed = time.time() - start_time
        
        # Check timeout
        if elapsed > timeout:
            logger.error(f"[Leonardo] Timeout after {elapsed:.1f}s")
            raise HTTPException(status_code=504, detail=f"Image generation timed out after {timeout}s")
        
        try:
            logger.info(f"[Leonardo] Poll attempt {attempt} (elapsed: {elapsed:.1f}s)")
            
            res = requests.get(
                f"{LEO_BASE_URL}/generations/{gen_id}",
                headers=LEO_HEADERS,
                timeout=30
            )
            
            if res.status_code != 200:
                logger.warning(f"[Leonardo] Poll returned status {res.status_code}: {res.text}")
                time.sleep(poll_interval)
                continue
            
            data = res.json()
            
            # Check generation status
            generation_data = data.get("generations_by_pk", {})
            status = generation_data.get("status")
            
            logger.info(f"[Leonardo] Generation status: {status}")
            
            # Check for failure
            if status == "FAILED":
                logger.error(f"[Leonardo] Generation failed: {generation_data}")
                raise HTTPException(status_code=500, detail="Image generation failed")
            
            # Check for completed images
            images = generation_data.get("generated_images", [])
            
            if images and len(images) > 0:
                image_url = images[0].get("url")
                if image_url:
                    logger.info(f"[Leonardo] Image ready: {image_url}")
                    return image_url
            
            # Wait before next poll
            logger.debug(f"[Leonardo] No images yet, waiting {poll_interval}s...")
            time.sleep(poll_interval)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[Leonardo] Poll error: {str(e)}")
            # Don't fail on poll errors, just retry
            time.sleep(poll_interval)
    
    raise HTTPException(status_code=500, detail="Unexpected exit from polling loop")


# ---------------- MAIN ROUTE ----------------
@app.post("/generate")
def generate(req: StoryRequest):
    """
    Main endpoint to generate illustration from story.
    
    Process:
    1. Send story to Backboard AI to generate image prompt
    2. Send prompt to Leonardo AI to create image
    3. Poll Leonardo until image is ready
    4. Return image URL and metadata
    """
    try:
        logger.info("="*60)
        logger.info(f"[MAIN] New request received")
        logger.info(f"[MAIN] Story length: {len(req.story)} characters")
        logger.info(f"[MAIN] Story preview: {req.story[:100]}...")
        
        # STEP 1: Backboard → prompt
        logger.info("[MAIN] Step 1: Generating prompt with Backboard...")
        prompt = generate_prompt_with_backboard(req.story)
        logger.info(f"[MAIN] Step 1 complete. Prompt: {prompt[:100]}...")
        
        # STEP 2: prompt → image generation
        logger.info("[MAIN] Step 2: Creating Leonardo generation...")
        gen_id = create_generation(prompt)
        logger.info(f"[MAIN] Step 2 complete. Generation ID: {gen_id}")
        
        # STEP 3: wait for image
        logger.info("[MAIN] Step 3: Waiting for image...")
        image_url = wait_for_image(gen_id)
        logger.info(f"[MAIN] Step 3 complete. Image URL: {image_url}")
        
        result = {
            "success": True,
            "story": req.story,
            "prompt": prompt,
            "image_url": image_url,
            "generation_id": gen_id
        }
        
        logger.info("[MAIN] ✓ Request completed successfully")
        logger.info("="*60)
        
        return result
        
    except HTTPException as he:
        logger.error(f"[MAIN] ✗ HTTPException: {he.status_code} - {he.detail}")
        logger.info("="*60)
        raise he
        
    except Exception as e:
        logger.error(f"[MAIN] ✗ Unexpected error: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info("="*60)
        
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# ---------------- HEALTH CHECK ----------------
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


# ---------------- STARTUP ----------------
@app.on_event("startup")
async def startup_event():
    logger.info("="*60)
    logger.info("Story Illustration Generator API Starting...")
    logger.info(f"Backboard URL: {BACKBOARD_URL}")
    logger.info(f"Assistant ID: {ASSISTANT_ID}")
    logger.info(f"Leonardo URL: {LEO_BASE_URL}")
    logger.info("="*60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)