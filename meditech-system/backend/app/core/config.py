from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Configuración centralizada de la aplicación MediTech System 3.0"""
    
    # Aplicación
    APP_NAME: str = "MediTech System"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Base de datos
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "meditech_db"
    DB_USER: str = "meditech_user"
    DB_PASSWORD: str = "meditech_secure_2024"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Seguridad JWT
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Orthanc (PACS)
    ORTHANC_URL: str = "http://localhost:8042"
    ORTHANC_USERNAME: str = "orthanc"
    ORTHANC_PASSWORD: str = "orthanc"
    
    # OpenELIS (LIS)
    OPENELIS_URL: str = "http://localhost:8080"
    OPENELIS_USERNAME: str = "admin"
    OPENELIS_PASSWORD: str = "admin!@#"
    
    # HL7 MLLP Server
    HL7_HOST: str = "0.0.0.0"
    HL7_PORT: int = 2575
    
    # Archivos
    UPLOAD_DIR: str = "/opt/meditech/uploads"
    RESULTS_DIR: str = "/opt/meditech/results"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://tu-dominio.com"
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Pagos
    STRIPE_SECRET_KEY: Optional[str] = None
    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_SECRET: Optional[str] = None
    
    # Email (opcional para notificaciones)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@meditech.com"
    
    # Multi-sucursal
    DEFAULT_BRANCH_ID_PREFIX: str = "001"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Singleton de configuración"""
    return Settings()
