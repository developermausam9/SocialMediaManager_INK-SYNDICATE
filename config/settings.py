from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    TELEGRAM_BOT_TOKEN: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    FB_PAGE_ID: str
    FB_ACCESS_TOKEN: str
    HF_API_KEY: str
    ALLOWED_TELEGRAM_USERS: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
