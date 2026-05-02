import requests
import time

API_KEY = "32f89283-536d-4deb-bf84-86252952a29b"

BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


# ---------------- STEP 1: CREATE GENERATION ----------------
def create_generation(prompt: str):
    payload = {
        "prompt": f"{prompt}, black and white pencil sketch, cinematic lighting, highly detailed",
        "modelId": "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3",
        "num_images": 1,
        "width": 1024,
        "height": 1024
    }

    response = requests.post(
        f"{BASE_URL}/generations",
        headers=HEADERS,
        json=payload
    )

    print("Create status:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        raise Exception("Failed to create generation")

    data = response.json()
    generation_id = data["sdGenerationJob"]["generationId"]

    print("Generation ID:", generation_id)
    return generation_id


# ---------------- STEP 2: POLL FOR RESULT ----------------
def wait_for_result(generation_id: str):
    print("Waiting for image...")

    while True:
        response = requests.get(
            f"{BASE_URL}/generations/{generation_id}",
            headers=HEADERS
        )

        if response.status_code != 200:
            print(response.text)
            raise Exception("Failed to fetch generation status")

        data = response.json()

        images = data["generations_by_pk"]["generated_images"]

        if images and len(images) > 0:
            image_url = images[0]["url"]
            print("\n✅ Image ready!")
            print("Image URL:", image_url)
            return image_url

        print("Still generating...")
        time.sleep(2)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    prompt = "A boy walking into a glowing magical forest at dusk"

    gen_id = create_generation(prompt)
    image_url = wait_for_result(gen_id)

    print("\nFINAL RESULT:")
    print(image_url)