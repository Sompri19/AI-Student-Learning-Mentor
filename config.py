"""
Application Configuration for AI Student Learning Mentor.
Loads settings from environment variables with safe defaults.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    """Base configuration class."""
    
    # Project Metadata
    PROJECT_NAME = "AI Student Learning Mentor"
    CURRENT_PHASE = 9

    # Environment
    ENV = os.getenv('FLASK_ENV', os.getenv('ENV', 'development')).lower().strip()

    # Database Configuration (PyMySQL / XAMPP)
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'student_learning_mentor')

    # Security Settings
    _DEV_SECRET_FALLBACK = 'change-this-secret-key'
    _RAW_SECRET = os.getenv('SECRET_KEY')
    if ENV in ('production', 'prod'):
        if not _RAW_SECRET or _RAW_SECRET.strip() == _DEV_SECRET_FALLBACK:
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION: A secure, random SECRET_KEY must be "
                "provided via environment variable in production environments. "
                "The default development fallback is forbidden."
            )
        SECRET_KEY = _RAW_SECRET.strip()
    else:
        SECRET_KEY = _RAW_SECRET.strip() if _RAW_SECRET else _DEV_SECRET_FALLBACK

    CSRF_ENABLED = os.getenv('CSRF_ENABLED', 'true').lower() == 'true'
    CSRF_STRICT = os.getenv('CSRF_STRICT', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', '86400'))

    # AI Provider Settings (Phase 6)
    # Supported providers: gemini, openai, groq, mock (tests only).
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini').lower().strip()
    AI_API_KEY = os.getenv('AI_API_KEY', '').strip()

    # Each provider has its own default model so switching AI_PROVIDER alone
    # never sends a foreign model name to the wrong API.
    _AI_PROVIDER_DEFAULT_MODELS = {
        'gemini': 'gemini-1.5-flash',
        'openai': 'gpt-3.5-turbo',
        'chatgpt': 'gpt-3.5-turbo',
        'groq': 'openai/gpt-oss-120b',
    }
    AI_MODEL = os.getenv(
        'AI_MODEL',
        _AI_PROVIDER_DEFAULT_MODELS.get(AI_PROVIDER, 'gemini-1.5-flash')
    ).strip()
    AI_RATE_LIMIT_SECONDS = int(os.getenv('AI_RATE_LIMIT_SECONDS', '5'))


class TestConfig(Config):
    """Testing configuration class."""
    TESTING = True
    DB_NAME = os.getenv('TEST_DB_NAME', Config.DB_NAME)
    AI_PROVIDER = 'mock'
    AI_API_KEY = 'test-mock-api-key'
    AI_RATE_LIMIT_SECONDS = 0
    CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
