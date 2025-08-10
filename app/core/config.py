"""
Application configuration
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "AssetDNA"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=10001, env="PORT")
    SECRET_KEY: str = Field(default="change-me-in-production", env="SECRET_KEY")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://assetdna:assetdna@localhost:5432/assetdna",
        env="DATABASE_URL"
    )
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS"
    )
    
    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=50 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 50MB
    UPLOAD_PATH: str = Field(default="uploads", env="UPLOAD_PATH")
    
    # URN Configuration
    URN_PREFIX: str = Field(default="urn:assetdna", env="URN_PREFIX")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# Create settings instance
settings = Settings()