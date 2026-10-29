import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base configuration with safe defaults."""
    SECRET_KEY = os.environ.get("SECRET_KEY") or "agriconnect-insecure-dev-fallback-key-change-me"
    
    # Database Configuration:
    # Use DATABASE_URL if set. In local dev, if PostgreSQL is not active, can fallback to SQLite.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'agriconnect.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security & Upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5 MB max upload
    UPLOAD_FOLDER = BASE_DIR / os.environ.get("UPLOAD_FOLDER", "app/static/uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # External Price Tracker Source Configuration
    AGRI_PRICE_API_KEY = os.environ.get("AGRI_PRICE_API_KEY", "")
    AGRI_PRICE_API_URL = os.environ.get("AGRI_PRICE_API_URL", "")


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False


from sqlalchemy.pool import StaticPool


class TestingConfig(Config):
    """Testing environment configuration with isolated in-memory test database."""
    DEBUG = False
    TESTING = True
    WTF_CSRF_ENABLED = False
    # Use StaticPool so SQLite in-memory persists across test requests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }


class ProductionConfig(Config):
    """Production environment configuration with strict security defaults."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

