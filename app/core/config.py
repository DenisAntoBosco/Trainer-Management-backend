from pydantic_settings import BaseSettings
from typing import Optional
import os
from .secrets import secretsmanager

class Settings(BaseSettings):
    database_url: Optional[str] = None
    secret_key: str = "sk_prod_trainer_mgmt_2024_secure_key_32_chars_min"
    
    # SMTP Email Configuration
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None
    
    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Get database URL from Secrets Manager if not provided
        if not self.database_url:
            self.database_url = secretsmanager.get_database_url()
        
        # Use the secret key from .env file consistently
        # Don't try to get from Secrets Manager since you don't have it there
        
        # Fallback to default if still not found
        if not self.database_url:
            self.database_url = "postgresql+asyncpg://postgres:1234554321@localhost:5432/neotrainer"

settings = Settings()

# Validate required settings
if not settings.database_url:
    raise ValueError("DATABASE_URL is required")