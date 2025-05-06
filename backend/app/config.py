from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """Application settings that can be loaded from environment variables."""
    
    APP_NAME: str = "Manim Visualization API"
    APP_VERSION: str = "1.0.0"
    RENDER_DIR: str = os.getenv("RENDER_DIR","/content/renders")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_BUCKET: str = os.getenv("SUPABASE_BUCKET", "manim-animations")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AIzaSyCI1mq-oDokjMVivlcXOXwlyQk-8uxK6jU")
    MANIM_QUALITY: str = "m"  # l=low, m=medium, h=high
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()