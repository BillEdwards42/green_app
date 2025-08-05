from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator
import os
from pathlib import Path


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Green Moment API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Green Moment Backend"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str
    DATABASE_SYNC_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Carbon Data Integration
    CARBON_DATA_PATH: Path = Path("/home/bill/StudioProjects/green_moment_integrated/stru_data")
    CARBON_DATA_UPDATE_INTERVAL: int = 600  # 10 minutes
    
    # Timezone
    TIMEZONE: str = "Asia/Taipei"
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH: str = "../firebase-admin-sdk.json"
    
    # Appliance power consumption (in Watts)
    APPLIANCE_POWER: dict = {
        "washing_machine": 500,
        "dryer": 2000,
        "dishwasher": 1800,
        "oven": 2400,
        "microwave": 1000,
        "rice_cooker": 700,
        "tv": 150,
        "air_conditioner": 1500,
        "fan": 75,
        "ev_fast_charge": 50000,
        "ev_slow_charge": 7000,
    }
    
    # League thresholds (kg CO2 saved)
    LEAGUE_THRESHOLDS: dict = {
        "bronze": 0,
        "silver": 10,
        "gold": 50,
        "platinum": 100,
        "diamond": 250,
    }
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()