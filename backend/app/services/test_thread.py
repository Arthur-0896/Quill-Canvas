import requests

API_KEY = "espr_8oGMKow5gEEFba8V7KpaR7Zh651S78qZq8RvILvRmQc"
BASE_URL = "https://app.backboard.io/api"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

ASSISTANT_ID = "a7d1ed13-a56d-4605-ba70-ddeef97efc22"

# Send first message (this auto-creates thread)
response = requests.post(
    f"{BASE_URL}/threads/messages",
    json={
        "assistant_id": ASSISTANT_ID,
        "content": "A boy walking into a glowing forest at dusk"
    },
    headers=HEADERS
)

data = response.json()

print("THREAD ID:", data.get("thread_id"))
print("OUTPUT:", data.get("content"))