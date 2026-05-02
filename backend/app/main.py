from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import time
import os
import logging
import tempfile
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from PIL import Image as PILImage

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


class PDFRequest(BaseModel):
    story: str
    image_url: str
    prompt: str = ""


# ---------------- BACKBOARD CALL ----------------
def generate_prompt_with_backboard(story: str, max_retries: int = 3) -> str:
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
            
            logger.info(f"[Backboard] Response status: {response.status_code}")
            
            if response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", 60))
                logger.warning(f"[Backboard] Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"[Backboard] Response data: {data}")
            
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
            time.sleep(2 ** attempt)
            
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
            
            if res.status_code == 429:
                wait_time = int(res.headers.get("Retry-After", 60))
                logger.warning(f"[Leonardo] Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
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
    start_time = time.time()
    attempt = 0
    
    logger.info(f"[Leonardo] Waiting for image generation: {gen_id}")
    
    while True:
        attempt += 1
        elapsed = time.time() - start_time
        
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
            
            generation_data = data.get("generations_by_pk", {})
            status = generation_data.get("status")
            
            logger.info(f"[Leonardo] Generation status: {status}")
            
            if status == "FAILED":
                logger.error(f"[Leonardo] Generation failed: {generation_data}")
                raise HTTPException(status_code=500, detail="Image generation failed")
            
            images = generation_data.get("generated_images", [])
            
            if images and len(images) > 0:
                image_url = images[0].get("url")
                if image_url:
                    logger.info(f"[Leonardo] Image ready: {image_url}")
                    return image_url
            
            logger.debug(f"[Leonardo] No images yet, waiting {poll_interval}s...")
            time.sleep(poll_interval)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[Leonardo] Poll error: {str(e)}")
            time.sleep(poll_interval)
    
    raise HTTPException(status_code=500, detail="Unexpected exit from polling loop")


# ---------------- MAIN ROUTE ----------------
@app.post("/generate")
def generate(req: StoryRequest):
    try:
        logger.info("="*60)
        logger.info(f"[MAIN] New request received")
        logger.info(f"[MAIN] Story length: {len(req.story)} characters")
        logger.info(f"[MAIN] Story preview: {req.story[:100]}...")
        
        logger.info("[MAIN] Step 1: Generating prompt with Backboard...")
        prompt = generate_prompt_with_backboard(req.story)
        logger.info(f"[MAIN] Step 1 complete. Prompt: {prompt[:100]}...")
        
        logger.info("[MAIN] Step 2: Creating Leonardo generation...")
        gen_id = create_generation(prompt)
        logger.info(f"[MAIN] Step 2 complete. Generation ID: {gen_id}")
        
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


# ---------------- PDF GENERATION ----------------
@app.post("/generate-pdf")
def generate_pdf(req: PDFRequest):
    """
    Generate a landscape A4 PDF with story and image side-by-side.
    """
    try:
        logger.info("="*60)
        logger.info("[PDF] Generating landscape PDF...")
        logger.info(f"[PDF] Story length: {len(req.story)} characters")
        logger.info(f"[PDF] Image URL: {req.image_url}")
        
        # Create temporary filenames (cross-platform)
        temp_dir = tempfile.gettempdir()
        pdf_filename = os.path.join(temp_dir, f"story_illustration_{int(time.time())}.pdf")
        temp_image_path = os.path.join(temp_dir, f"temp_image_{int(time.time())}.png")
        
        logger.info(f"[PDF] Temp dir: {temp_dir}")
        logger.info(f"[PDF] PDF path: {pdf_filename}")
        logger.info(f"[PDF] Image path: {temp_image_path}")
        
        # Download image
        logger.info("[PDF] Downloading image...")
        img_response = requests.get(req.image_url, timeout=30)
        img_response.raise_for_status()
        
        # Save image temporarily
        with open(temp_image_path, "wb") as f:
            f.write(img_response.content)
        
        logger.info(f"[PDF] Image saved successfully")
        
        # Verify image file exists
        if not os.path.exists(temp_image_path):
            raise Exception(f"Image file not created: {temp_image_path}")
        
        # Create PDF with landscape A4 format
        doc = SimpleDocTemplate(
            pdf_filename,
            pagesize=landscape(A4),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Get page dimensions
        page_width, page_height = landscape(A4)
        logger.info(f"[PDF] Page size: {page_width} x {page_height}")
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#111111'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        story_style = ParagraphStyle(
            'StoryStyle',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            spaceAfter=10,
            alignment=TA_LEFT
        )
        
        # Build content for side-by-side layout
        from reportlab.platypus import Frame, PageTemplate
        from reportlab.pdfgen import canvas as pdf_canvas
        
        # Custom function to build the PDF with two-column layout
        def build_two_column_pdf():
            c = pdf_canvas.Canvas(pdf_filename, pagesize=landscape(A4))
            page_width, page_height = landscape(A4)
            
            # Define margins and column width
            margin = 0.5 * inch
            column_width = (page_width - 3 * margin) / 2  # Split into 2 columns with gap
            
            # LEFT SIDE: Story
            x_left = margin
            y_start = page_height - margin - 30  # Start below title
            
            # Draw title
            c.setFont("Helvetica-Bold", 20)
            c.drawString(page_width / 2 - 100, page_height - margin, "Your Story & Illustration")
            
            # Draw story text on left
            c.setFont("Helvetica", 10)
            y_position = y_start
            line_height = 14
            max_width = column_width
            
            for paragraph in req.story.split('\n'):
                if paragraph.strip():
                    # Word wrap the paragraph
                    words = paragraph.split()
                    line = ""
                    for word in words:
                        test_line = line + word + " "
                        if c.stringWidth(test_line, "Helvetica", 10) < max_width:
                            line = test_line
                        else:
                            c.drawString(x_left, y_position, line.strip())
                            y_position -= line_height
                            line = word + " "
                            
                            if y_position < margin:
                                break
                    
                    if line.strip():
                        c.drawString(x_left, y_position, line.strip())
                        y_position -= line_height
                    
                    y_position -= line_height * 0.5  # Extra space between paragraphs
                    
                    if y_position < margin:
                        break
            
            # RIGHT SIDE: Image
            x_right = margin + column_width + margin
            
            try:
                # Load and scale image
                img = PILImage.open(temp_image_path)
                img_width, img_height = img.size
                
                # Calculate scaling to fit right column
                available_width = column_width
                available_height = page_height - 2 * margin - 40  # Account for title
                
                scale = min(available_width / img_width, available_height / img_height)
                scaled_width = img_width * scale
                scaled_height = img_height * scale
                
                # Center the image in the right column (both horizontally and vertically)
                x_img = x_right + (column_width - scaled_width) / 2
                y_img = margin + (available_height - scaled_height) / 2
                
                logger.info(f"[PDF] Drawing image at ({x_img}, {y_img}) size {scaled_width}x{scaled_height}")
                
                c.drawImage(temp_image_path, x_img, y_img, 
                           width=scaled_width, height=scaled_height, 
                           preserveAspectRatio=True)
                
            except Exception as e:
                logger.error(f"[PDF] Error drawing image: {str(e)}")
                c.setFont("Helvetica", 12)
                c.drawString(x_right, page_height / 2, "Error loading image")
            
            # Save PDF
            c.save()
            logger.info("[PDF] PDF saved successfully")
        
        # Build the PDF
        build_two_column_pdf()
        
        # Clean up temp image
        try:
            os.remove(temp_image_path)
            logger.info("[PDF] Cleaned up temp image")
        except Exception as e:
            logger.warning(f"[PDF] Could not delete temp image: {e}")
        
        logger.info(f"[PDF] ✓ PDF generated: {pdf_filename}")
        logger.info("="*60)
        
        # Return PDF file
        return FileResponse(
            pdf_filename,
            media_type='application/pdf',
            filename=f"story_illustration_{int(time.time())}.pdf",
            headers={
                "Content-Disposition": f"attachment; filename=story_illustration.pdf"
            }
        )
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[PDF] ✗ Error downloading image: {str(e)}")
        logger.info("="*60)
        raise HTTPException(status_code=502, detail=f"Failed to download image: {str(e)}")
        
    except Exception as e:
        logger.error(f"[PDF] ✗ Error generating PDF: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info("="*60)
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")


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