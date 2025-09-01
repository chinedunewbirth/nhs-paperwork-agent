"""
Configuration and Settings for NHS Paperwork Automation Agent
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "NHS Paperwork Automation Agent"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/nhs_agent.db")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File Storage
    upload_dir: str = "./data/uploads"
    forms_dir: str = "./data/forms"
    templates_dir: str = "./templates"
    
    # NHS Compliance
    data_retention_days: int = 30
    audit_log_enabled: bool = True
    encryption_enabled: bool = True
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Streamlit Configuration
    streamlit_host: str = "localhost"
    streamlit_port: int = 8501
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()


def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        settings.upload_dir,
        settings.forms_dir,
        settings.templates_dir,
        "./data"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
