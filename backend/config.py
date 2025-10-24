"""
Configuration management for Flask application
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
LOGS_DIR = Path(os.getenv("LOGS_DIR", str(BASE_DIR / "logs")))

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True, parents=True)
LOGS_DIR.mkdir(exist_ok=True, parents=True)


class Config:
    """Application configuration"""

    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")
    DEBUG = os.getenv("FLASK_ENV", "production") == "development"

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "86400"))  # 24 hours

    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "qa_search.db"))

    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", str(LOGS_DIR / "app.log"))

    # CORS
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5000"]

    # Pagination
    RESULTS_PER_PAGE = 20
    MAX_RESULTS_PER_PAGE = 100

    # Testing Credentials (REMOVE IN PRODUCTION!)
    # Set these in .env for automatic test user creation
    TEST_USERNAME = os.getenv("TEST_USERNAME", "")
    TEST_PASSWORD = os.getenv("TEST_PASSWORD", "")

    @staticmethod
    def validate():
        """Validate critical configuration"""
        errors = []

        if not Path(Config.DATABASE_PATH).exists():
            errors.append(f"Database not found at: {Config.DATABASE_PATH}")

        if Config.SECRET_KEY == "change-this-secret-key":
            errors.append("FLASK_SECRET_KEY not set in .env file")

        if Config.JWT_SECRET_KEY == "change-this-jwt-secret":
            errors.append("JWT_SECRET_KEY not set in .env file")

        return errors


# Export config instance
config = Config()
