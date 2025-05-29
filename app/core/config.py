from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Orquix Backend"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"
    
    # Database
    ORQUIX_DB_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/orquix_db"
    
    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Auth
    GOOGLE_CLIENT_ID: str = "tu_google_client_id"
    GOOGLE_CLIENT_SECRET: str = "tu_google_client_secret"
    JWT_PUBLIC_KEY: str = "clave_publica_de_nextauth"
    JWT_ALGORITHM: str = "RS256"
    
    @property
    def sync_database_url(self) -> str:
        return self.ORQUIX_DB_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    @property
    def async_database_url(self) -> str:
        return self.ORQUIX_DB_URL

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)


settings = Settings() 