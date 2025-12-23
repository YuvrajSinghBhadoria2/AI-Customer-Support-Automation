from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/support_db"
    
    # LLM Provider
    llm_provider: Literal["groq"] = "groq"
    groq_api_key: str
    groq_model: str = "llama-3.1-70b-versatile"
    
    # Gmail API
    gmail_credentials_file: str = "credentials.json"
    gmail_token_file: str = "token.json"
    support_email: str
    
    # Application Settings
    backend_port: int = 8000
    dashboard_port: int = 8501
    auto_send_threshold: float = 0.8
    escalation_threshold: float = 0.6
    
    # SLA Settings (in hours)
    sla_low: int = 48
    sla_medium: int = 24
    sla_high: int = 8
    sla_critical: int = 2
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
