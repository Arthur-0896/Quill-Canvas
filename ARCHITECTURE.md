# Real-Time Story Editor Architecture

## System Overview

```
┌─────────────────────────────────────────┐
│   React Frontend (Story Editor)          │
│  ┌──────────────┬──────────────────────┐ │
│  │ Story Input  │  Image Preview        │ │
│  │ (Left Pane)  │  (Right Pane)         │ │
│  └──────────────┴──────────────────────┘ │
│           ↕ WebSocket (Real-time)        │
└─────────────────────────────────────────┘
           ↓ ws://localhost:8000/api/editor/ws/{story_id}

┌─────────────────────────────────────────┐
│   FastAPI Backend (WebSocket Server)     │
├─────────────────────────────────────────┤
│  • ConnectionManager (WebSocket sessions)│
│  • Real-time Scene Extraction            │
│  • AWS Bedrock Image Generation          │
│  • Database (Story/Scene tracking)       │
│  • S3 Storage (Generated images)         │
└──────────┬──────────┬──────────┬─────────┘
           ↓          ↓          ↓
        RDS        S3      AWS Bedrock
```

## Features

### 1. **Real-Time Text Processing**
- User types in left pane
- Debounced input (1.5s) to avoid overwhelming backend
- Automatic scene detection as user writes

### 2. **Dynamic Image Generation**
- Scene extraction from story text
- Creates detailed prompts for each scene
- AWS Bedrock Titan generates images
- Displays in right pane in real-time

### 3. **WebSocket Communication**
- Persistent bidirectional connection
- Server pushes updates as images generate
- Client keeps connection alive with ping/pong

### 4. **Scene Management**
- Detects multiple scenes from story
- Tracks scene order and metadata
- Gallery view of all generated images
- Easy navigation between scenes

## Backend Setup

### Prerequisites
```bash
# Python 3.11+
# AWS Account with Bedrock access
# PostgreSQL (optional, for persistence)
```

### Environment Variables (.env)
```
# AWS Credentials
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

# Backboard Integration
BACKBOARD_API_KEY=your_key
BACKBOARD_ASSISTANT_ID=your_id
BACKBOARD_WORKFLOW_ID=your_workflow
BACKBOARD_BASE_URL=https://app.backboard.io/api

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost/quill_canvas
```

### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Required Packages
```
fastapi==0.111.3
uvicorn[standard]==0.23.0
websockets==12.0
pydantic-settings==2.0.0
boto3==1.28.0  # AWS SDK
sqlalchemy==2.0.0  # ORM
python-dotenv==1.0.0
```

### Run Backend
```bash
# From project root (Quill-Canvas/)
PYTHONPATH=. python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/docs (Swagger UI)

## Frontend Setup

### Prerequisites
```bash
# Node.js 16+
# npm or yarn
```

### Install Dependencies
```bash
cd frontend
npm install
```

### Run Frontend
```bash
npm start
```

Visit: http://localhost:3000

## WebSocket Message Protocol

### Client → Server

**1. Story Update** (sent on text input with 1.5s debounce)
```json
{
  "type": "story_update",
  "title": "The Lost Library",
  "author": "Jane Doe",
  "content": "Once upon a time..."
}
```

**2. Keep-Alive**
```json
{
  "type": "ping"
}
```

### Server → Client

**1. Processing Started**
```json
{
  "type": "processing_started",
  "message": "Analyzing story and detecting scenes..."
}
```

**2. Scene Detected**
```json
{
  "type": "scene_detected",
  "scene_id": "scene-uuid",
  "sequence": 1,
  "title": "Discovery",
  "description": "...",
  "image_prompt": "..."
}
```

**3. Image Generating**
```json
{
  "type": "image_generating",
  "scene_id": "scene-uuid",
  "message": "Generating image for: Discovery..."
}
```

**4. Image Generated**
```json
{
  "type": "image_generated",
  "scene_id": "scene-uuid",
  "image_base64": "data:image/png;base64,...",
  "image_prompt": "..."
}
```

**5. Processing Completed**
```json
{
  "type": "processing_completed",
  "total_scenes": 3,
  "message": "Story processing completed!"
}
```

**6. Error**
```json
{
  "type": "error",
  "error": "Failed to generate image"
}
```

## API Endpoints

### REST Endpoints
```
GET  /api/health                    # Health check
POST /api/story/preview             # Get scene preview (without images)
POST /api/story/launch              # Launch full Backboard workflow
GET  /api/test/t                    # Test endpoint
```

### WebSocket Endpoint
```
WS   /api/editor/ws/{story_id}      # Real-time editor connection
```

## Database Schema

### Stories Table
```sql
CREATE TABLE stories (
  id VARCHAR PRIMARY KEY,
  user_id VARCHAR,
  title VARCHAR(255),
  content TEXT,
  status ENUM('draft', 'processing', 'completed', 'failed'),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### Scenes Table
```sql
CREATE TABLE scenes (
  id VARCHAR PRIMARY KEY,
  story_id VARCHAR NOT NULL,
  sequence INTEGER,
  title VARCHAR(255),
  description TEXT,
  image_prompt TEXT,
  image_url VARCHAR(500),
  status ENUM('detected', 'generating', 'completed', 'failed'),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

## AWS Configuration

### Bedrock Setup
1. Enable Bedrock in AWS Console
2. Request access to Titan Image Generator model
3. Get AWS credentials with `bedrock:InvokeModel` permission

### S3 Bucket
Create bucket: `quill-canvas-images`
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::quill-canvas-images/*"
    }
  ]
}
```

## Performance Optimization

### Debouncing
- 1.5 second debounce on text input
- Prevents excessive backend processing
- Smooth user experience

### Image Caching
- S3 stores generated images
- Reuse images for similar prompts
- Pre-signed URLs for direct download

### Pagination
- Gallery shows all scenes as thumbnails
- Load full resolution on demand

## Scaling Considerations

### Current (Development)
- Single FastAPI server
- In-memory WebSocket connections
- Suitable for <100 concurrent users

### Production Options

**Option 1: Add Database**
- Store scenes/images in PostgreSQL
- Enable persistence across restarts
- Track user submissions

**Option 2: Scale WebSocket**
- Use Redis for cross-server messaging
- Deploy multiple FastAPI instances
- Load balance with nginx

**Option 3: Async Queue**
- Move image generation to background job queue (Celery/RabbitMQ)
- WebSocket sends progress updates
- Support unlimited concurrent users

## Troubleshooting

### WebSocket Connection Issues
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Verify CORS settings in main.py
```

### Image Generation Fails
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify Bedrock model access
aws bedrock list-foundation-models
```

### Scene Extraction Issues
- Check story text length (minimum 200 chars)
- Verify story has clear scene breaks (paragraphs)
- Check story_processor.py logic

## Example Usage

1. **Start Backend**
   ```bash
   PYTHONPATH=. python -m uvicorn backend.app.main:app --reload
   ```

2. **Start Frontend**
   ```bash
   npm start
   ```

3. **Open Browser**
   - Go to http://localhost:3000
   - Start typing a story
   - Watch images generate in real-time on the right

## File Structure

```
Quill-Canvas/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   │           ├── editor.py      # WebSocket endpoint
│   │   │           ├── story.py       # Story endpoints
│   │   │           └── test.py
│   │   ├── models/
│   │   │   └── story_models.py        # Database models
│   │   ├── services/
│   │   │   ├── ai/
│   │   │   │   └── bedrock_generator.py  # Image generation
│   │   │   ├── websocket_manager.py  # WebSocket logic
│   │   │   └── story_processor.py    # Scene extraction
│   │   ├── config.py
│   │   └── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── StoryEditor.tsx       # Main component
│   │   │   └── StoryEditor.css       # Styling
│   │   └── App.tsx
│   └── package.json
│
└── README.md
```

## License

MIT
