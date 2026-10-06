import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database credentials from environment
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "farmlink_db")
DB_PORT = os.getenv("DB_PORT", "3306")

# URL-encode user and password to safely handle special characters (e.g., @, :, /)
_encoded_user = quote_plus(DB_USER)
_encoded_password = quote_plus(DB_PASSWORD)

# Construct SQLAlchemy Database URI
SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{_encoded_user}:{_encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# SQLAlchemy configuration
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Application Secret Key with default fallback
SECRET_KEY = os.getenv("SECRET_KEY", "farmlink-default-secret-key-change-in-production")


class Config:
    """Base configuration class for Flask / SQLAlchemy applications."""

    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = SQLALCHEMY_TRACK_MODIFICATIONS

    # Recommended engine options for resilient MySQL connections
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }
