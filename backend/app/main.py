from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import time
import os

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
def generate_prompt_with_backboard(story: str):

    response = requests.post(
        f"{BACKBOARD_URL}/threads/messages",
        headers=HEADERS,
        json={"content": story}
    )

    data = response.json()

    # Backboard returns structured message
    prompt = data.get("content") or data.get("response") or str(data)

    return prompt


# ---------------- LEONARDO ----------------
def create_generation(prompt: str):

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
        json=payload
    )

    if res.status_code != 200:
        raise Exception(res.text)

    return res.json()["sdGenerationJob"]["generationId"]


def wait_for_image(gen_id: str):

    while True:
        res = requests.get(
            f"{LEO_BASE_URL}/generations/{gen_id}",
            headers=LEO_HEADERS
        )

        if res.status_code != 200:
            raise Exception(res.text)

        data = res.json()

        images = data["generations_by_pk"]["generated_images"]

        if images and len(images) > 0:
            return images[0]["url"]

        time.sleep(2)


# ---------------- MAIN ROUTE ----------------
@app.post("/generate")
def generate(req: StoryRequest):

    try:
        # STEP 1: Backboard → prompt
        prompt = generate_prompt_with_backboard(req.story)

        # STEP 2: prompt → image
        gen_id = create_generation(prompt)

        # STEP 3: wait for image
        image_url = wait_for_image(gen_id)

        return {
            "story": req.story,
            "prompt": prompt,
            "image_url": image_url
        }

    except Exception as e:
        return {
            "error": str(e)
        }