from pydantic_settings import BaseSettings
from typing import Optional
import os
from .secrets import secretsmanager

class Settings(BaseSettings):
    database_url: Optional[str] = None
    secret_key: str = "your-secret-key-change-in-production-min-32-chars"
    
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
        
        # Get secret key from Secrets Manager if not provided
        if self.secret_key == "your-secret-key-change-in-production-min-32-chars":
            secret_key = secretsmanager.get_secret_key()
            if secret_key:
                self.secret_key = secret_key
        
        # Fallback to default if still not found
        if not self.database_url:
            self.database_url = "postgresql+asyncpg://postgres:1234554321@localhost:5432/neotrainer"

settings = Settings()

# Validate required settings
if not settings.database_url:
    raise ValueError("DATABASE_URL is required")