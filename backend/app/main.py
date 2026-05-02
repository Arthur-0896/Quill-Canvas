from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()   # ✅ MUST be first

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CONFIG
API_KEY = "espr_8oGMKow5gEEFba8V7KpaR7Zh651S78qZq8RvILvRmQc"
BASE_URL = "https://app.backboard.io/api"
ASSISTANT_ID = "9b6415dc-79dd-468f-8399-4fb57306be4e"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# REQUEST MODEL
class StoryRequest(BaseModel):
    story: str


# ROUTE
@app.post("/generate")
def generate(req: StoryRequest):
    try:
        url = f"{BASE_URL}/threads/messages"

        payload = {
            "assistant_id": ASSISTANT_ID,
            "content": req.story
        }

        response = requests.post(
            url,
            headers=HEADERS,
            json=payload,
            timeout=30
        )

        # 🔴 ALWAYS log raw response first
        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        # If Backboard fails, return full error (NOT masked)
        if response.status_code != 200:
            return {
                "error": "Backboard request failed",
                "status_code": response.status_code,
                "raw_response": response.text
            }

        try:
            data = response.json()
        except Exception:
            return {
                "error": "Invalid JSON from Backboard",
                "raw_response": response.text
            }

        return {
            "output": data,
            "thread_id": data.get("thread_id")
        }

    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "trace": traceback.format_exc()
        }