import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "demo-secret-key-change-me")
    DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "app.db"))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "private_uploads"))
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    AI_API_URL = os.getenv("AI_API_URL", "")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
    APP_NAME = "Save Children’s Lives"
