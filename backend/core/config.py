import os
from typing import Optional


def get_env_bool(key: str, default: str = "False") -> bool:
    """Get boolean value from environment variable."""
    return os.getenv(key, default).lower() in ("true", "1", "yes")


def get_env_int(key: str, default: int) -> int:
    """Get integer value from environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


# =============================================================================
# Application Configuration
# =============================================================================
APP_NAME = os.getenv("APP_NAME", "NEW Fridge API")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = get_env_bool("DEBUG", "True")

# =============================================================================
# Security & Authentication
# =============================================================================
# JWT Configuration
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "your-secret-key-change-this-in-production-use-openssl-rand-hex-32"
)
ALGORITHM = "HS256"  # JWT algorithm (HS256 is standard)
ACCESS_TOKEN_EXPIRE_MINUTES = get_env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 1440)  # 24 hours

# BCrypt Configuration
BCRYPT_ROUNDS = get_env_int("BCRYPT_ROUNDS", 12)  # Cost factor (10-15)

# =============================================================================
# Database Configuration
# =============================================================================
# PostgreSQL (Primary Database)
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = get_env_int("POSTGRES_PORT", 5432)

# MongoDB (Analytics & Logging)
MONGO_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "password")
MONGO_HOST = os.getenv("MONGO_HOST", "mongodb")
MONGO_PORT = get_env_int("MONGO_PORT", 27017)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "newfridge")

# =============================================================================
# API Server Configuration
# =============================================================================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = get_env_int("API_PORT", 8000)
API_RELOAD = get_env_bool("API_RELOAD", "True")

# =============================================================================
# Logging Configuration
# =============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# =============================================================================
# CORS Configuration
# =============================================================================
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []

# =============================================================================
# Application Constants (These don't change)
# =============================================================================
# User Status
USER_STATUS_ACTIVE = "Active"
USER_STATUS_DISABLED = "Disabled"

# User Roles
USER_ROLE_USER = "User"
USER_ROLE_ADMIN = "Admin"

# Fridge Access Roles
FRIDGE_ROLE_OWNER = "Owner"
FRIDGE_ROLE_MEMBER = "Member"

# Standard Units
UNIT_GRAMS = "g"
UNIT_MILLILITERS = "ml"
UNIT_PIECES = "pcs"

# Order Status
ORDER_STATUS_PENDING = "Pending"
ORDER_STATUS_PROCESSING = "Processing"
ORDER_STATUS_SHIPPED = "Shipped"
ORDER_STATUS_DELIVERED = "Delivered"
ORDER_STATUS_CANCELLED = "Cancelled"
