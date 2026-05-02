from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# Load env
load_dotenv()

BACKBOARD_URL = "https://app.backboard.io/api"
ASSISTANT_ID = "6d159174-c4c3-4e90-b175-a0fdcd07ae0d"
API_KEY = "espr__3811pltJF5EDobQT0L0pWa-CPGfDkU83hwxTKUe394"

app = FastAPI()

# CORS (for React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StoryRequest(BaseModel):
    story: str


@app.post("/generate")
def generate(req: StoryRequest):
    try:
        url = f"{BACKBOARD_URL}/assistant/run"

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "assistant_id": ASSISTANT_ID,
                "messages": [
                    {
                        "role": "user",
                        "content": req.story
                    }
                ]
            },
            timeout=30
        )

        if response.status_code != 200:
            return {
                "output": f"Backboard error: {response.status_code} - {response.text}"
            }

        data = response.json()

        # 🔍 Debug once if needed
        # print(data)

        # Extract response safely
        output = (
            data.get("output")
            or data.get("response")
            or data.get("result")
            or data.get("data", {}).get("output")
            or str(data)
        )

        return {"output": output}

    except Exception as e:
        return {"output": f"Server error: {str(e)}"}