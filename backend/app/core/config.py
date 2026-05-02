import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# base directory
BASE_DIR = Path(__file__).resolve().parent

# environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# API settings
API_TITLE = "Cooking Assistant API"
API_VERSION = "0.1.0"
API_DESCRIPTION = "ML-powered recipe recommendation system"

# CORS origins
if IS_PRODUCTION:
    CORS_ORIGINS = [
        "https://*.vercel.app",
        "https://cooking-assistant.vercel.app",  # Your actual domain
    ]
else:
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

# Logging
LOG_LEVEL = "INFO" if IS_PRODUCTION else "DEBUG"