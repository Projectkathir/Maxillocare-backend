import os
from pathlib import Path
from dotenv import load_dotenv

# Force load .env from project root (Windows compatibility)
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Verify API key is loaded (for debugging)
if not os.getenv("GEMINI_API_KEY"):
    print("⚠️ WARNING: GEMINI_API_KEY not found in .env file!")
    print(f"⚠️ Looking for .env at: {env_path.absolute()}")
else:
    print(f"✅ GEMINI_API_KEY loaded successfully from .env")

# Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24  # 30 days

# File Upload
UPLOAD_DIR = "uploads/patient_images"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# Gemini AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"  # ✅ Updated to current model (Active since April 2025)
