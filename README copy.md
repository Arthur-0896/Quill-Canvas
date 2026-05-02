# Quill Canvas Backend

A FastAPI scaffold for the Quill Canvas storybook generation backend.

## Overview

This backend exposes endpoints for:
- scene extraction from story text
- AI image generation orchestration
- PDF composition
- integration with Backboard.io pipeline execution

It is intentionally scaffolded with placeholders so you can connect the business logic and AI services later.

## Getting Started

1. Create a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app locally:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Open the interactive docs:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

## Backboard.io Integration

The scaffold includes `app/backboard.py` as a starting point for calling Backboard pipelines.
Copy `.env.sample` to `.env` and set the values before running:

- `BACKBOARD_API_KEY`
- `BACKBOARD_WORKFLOW_ID`
- `BACKBOARD_BASE_URL` (optional, defaults to `https://api.backboard.io`)

## API Endpoints

- `POST /api/story/preview` — analyze story text and return a draft of scene metadata
- `POST /api/story/launch` — submit a story job to Backboard for full processing
- `GET /api/health` — health check
