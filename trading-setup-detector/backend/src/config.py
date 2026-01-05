from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./trading_detector.db"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # Anthropic
    anthropic_api_key: str = ""

    # Binance
    binance_api_key: str = ""
    binance_api_secret: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    # Scanner
    scan_interval_minutes: int = 5

    # Uploads
    upload_dir: str = "uploads"
    patterns_dir: str = "uploads/patterns"
    charts_dir: str = "uploads/charts"

    # Solana / Helius
    helius_api_key: str = ""
    helius_webhook_secret: str = ""

    # App URL (for webhook callbacks)
    app_base_url: str = "http://localhost:8000"

    # Solana charts
    solana_charts_dir: str = "uploads/solana_charts"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
