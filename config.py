import os
from dotenv import load_dotenv

load_dotenv()

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

# AI Service (for future integration)
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:5000")