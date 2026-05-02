# Quill Canvas - Setup & Deployment Guide

## Quick Start

### Local Development (Manual Setup)

#### 1. Backend Setup

```bash
# Navigate to project root
cd Quill-Canvas

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Create .env file with AWS credentials
cat > .env << EOF
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
BACKBOARD_API_KEY=your_key
BACKBOARD_ASSISTANT_ID=your_id
BACKBOARD_WORKFLOW_ID=your_workflow
BACKBOARD_BASE_URL=https://app.backboard.io/api
ENVIRONMENT=development
EOF

# Start backend server
PYTHONPATH=. python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend running at: **http://localhost:8000**
Swagger docs: **http://localhost:8000/docs**

#### 2. Frontend Setup

```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start React development server
npm start
```

Frontend running at: **http://localhost:3000**

---

### Docker Compose (Recommended)

One-command setup with PostgreSQL, Redis, backend, and frontend:

```bash
# From project root
docker-compose up -d

# View logs
docker-compose logs -f backend

# Access:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

Stop services:
```bash
docker-compose down
```

---

## AWS Configuration

### Step 1: Set Up AWS Account
1. Create AWS account at https://aws.amazon.com
2. Create IAM user with programmatic access
3. Attach policy: `AmazonBedrockFullAccess`

### Step 2: Enable Bedrock Models
1. Go to AWS Console → Bedrock
2. Click "Model access"
3. Request access to:
   - **Amazon Titan Image Generator G1** (for image generation)
   - **Anthropic Claude** (optional, for scene extraction)

### Step 3: Create S3 Bucket
```bash
aws s3 mb s3://quill-canvas-images --region us-east-1

# Set public read policy
aws s3api put-bucket-policy \
  --bucket quill-canvas-images \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::quill-canvas-images/*"
    }]
  }'
```

### Step 4: Update .env
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

---

## Architecture Overview

```
User Browser (React)
    ↓ WebSocket
FastAPI Server (Python)
    ↓ HTTP
AWS Bedrock (Image Generation)
S3 Bucket (Image Storage)
PostgreSQL (Data Persistence)
Backboard.io (Workflow Orchestration)
```

---

## Real-Time Flow

1. **User Types Story** → Text sent to backend via WebSocket
2. **Scene Detection** → Backend extracts key scenes from text
3. **Image Generation** → Each scene sent to AWS Bedrock
4. **Stream Updates** → Images streamed back in real-time
5. **Display on Right** → Images appear in preview pane as they generate

---

## API Endpoints

### REST API

```bash
# Health check
curl http://localhost:8000/api/health

# Preview scenes (no images)
curl -X POST http://localhost:8000/api/story/preview \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Story",
    "author": "Me",
    "text": "Once upon a time..."
  }'

# Launch full workflow with Backboard
curl -X POST http://localhost:8000/api/story/launch \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Story",
    "author": "Me",
    "text": "Once upon a time..."
  }'
```

### WebSocket API

Connection: `ws://localhost:8000/api/editor/ws/{story_id}`

**Client Message:**
```json
{
  "type": "story_update",
  "title": "The Lost Library",
  "author": "Jane Doe",
  "content": "Once upon a time in a hidden village..."
}
```

**Server Response:**
```json
{
  "type": "image_generated",
  "scene_id": "scene-123",
  "image_base64": "data:image/png;base64,iVBORw0KGgo...",
  "image_prompt": "A magical library with glowing books..."
}
```

---

## Deployment Options

### Option 1: AWS ECS (Elastic Container Service)

```bash
# Push Docker images to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker build -t quill-backend backend/
docker tag quill-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/quill-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/quill-backend:latest

# Create ECS task definition (see ECS console)
# Deploy with 2+ instances for HA
```

### Option 2: AWS Lambda + API Gateway

For stateless processing (requires refactoring for 15min timeout):

```bash
# Create Lambda function
zip -r backend.zip backend/
aws lambda create-function \
  --function-name quill-canvas \
  --runtime python3.11 \
  --handler backend.app.main.handler \
  --zip-file fileb://backend.zip
```

### Option 3: Heroku

```bash
heroku create quill-canvas
git push heroku main
heroku config:set AWS_ACCESS_KEY_ID=...
heroku logs --tail
```

### Option 4: Railway.app

1. Connect GitHub repo
2. Create backend and frontend services
3. Set environment variables
4. Deploy

---

## Database Migrations

For production (with PostgreSQL):

```bash
# Install Alembic
pip install alembic

# Create migrations
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

---

## Monitoring & Logs

### Local Development
```bash
# Backend logs (stdout)
# Shows request details and WebSocket events

# Frontend console (browser DevTools)
# Network tab shows WebSocket messages
```

### Production
```bash
# CloudWatch (AWS)
aws logs tail /aws/ecs/quill-canvas --follow

# Docker logs
docker logs quill-canvas-backend-1 -f
```

---

## Performance Tuning

### Frontend
- Lazy load image gallery
- Debounce text input (1.5s)
- Compress images for transfer

### Backend
- Use connection pooling (SQLAlchemy)
- Redis caching for repeated prompts
- Batch image generation if needed

### AWS
- Use Titan Image Generator (faster than Stable Diffusion)
- Cache generated images in S3
- Use CloudFront for CDN

---

## Troubleshooting

### WebSocket Connection Fails
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Browser console: Network tab → WS
# Look for 101 Switching Protocols status
```

### Images Not Generating
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify Bedrock access
aws bedrock list-foundation-models

# Check backend logs for AWS errors
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U quill_user -d quill_canvas

# Check Docker compose health
docker-compose ps

# View database logs
docker-compose logs postgres
```

### CORS Issues
```bash
# Backend logs will show CORS errors
# Make sure frontend origin is allowed in config.py
```

---

## File Structure

```
Quill-Canvas/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── editor.py         # WebSocket real-time
│   │   │   ├── story.py          # Story processing
│   │   │   └── test.py
│   │   ├── models/
│   │   │   └── story_models.py   # Database schemas
│   │   ├── services/
│   │   │   ├── ai/
│   │   │   │   └── bedrock_generator.py
│   │   │   ├── websocket_manager.py
│   │   │   └── story_processor.py
│   │   ├── config.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── StoryEditor.tsx
│   │   │   └── StoryEditor.css
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
├── ARCHITECTURE.md
└── README.md
```

---

## Next Steps

1. **Set up AWS credentials** ✓
2. **Install Docker & Docker Compose** ✓
3. **Run `docker-compose up`** ✓
4. **Open http://localhost:3000** ✓
5. **Start typing in the story editor** ✓

For production deployment, see deployment options above.

---

## Support

- Bedrock docs: https://docs.aws.amazon.com/bedrock/
- FastAPI docs: https://fastapi.tiangolo.com/
- React docs: https://react.dev/
- WebSocket guide: https://fastapi.tiangolo.com/advanced/websockets/

