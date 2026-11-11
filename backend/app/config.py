import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Women Safety Alert System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-women-safety-system-jwt-2025")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database config: defaults to SQLite for local file-based simplicity, but supports MySQL URL:
    # mysql+pymysql://username:password@localhost:3306/smart_safety_db
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./smart_safety.db"
    )

    # External Notification API Keys placeholder indicators
    FIREBASE_SERVER_KEY: str = os.getenv("FIREBASE_SERVER_KEY", "DEMO_FIREBASE_KEY_NOT_CONFIGURED")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "DEMO_TWILIO_SID_NOT_CONFIGURED")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "DEMO_TWILIO_TOKEN_NOT_CONFIGURED")
    TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "+10000000000")

    class Config:
        case_sensitive = True

settings = Settings()
