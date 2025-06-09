from typing import Optional, List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Orquix Backend"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database - Soporta tanto variables individuales como DATABASE_URL directo (Render)
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_PORT: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    
    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Auth
    GOOGLE_CLIENT_ID: str = "tu_google_client_id"
    GOOGLE_CLIENT_SECRET: str = "tu_google_client_secret"
    JWT_PUBLIC_KEY: str = "clave_publica_de_nextauth"
    JWT_ALGORITHM: str = "RS256"
    
    # Configuración de Context Manager
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Modelo a usar para embeddings
    EMBEDDING_DIMENSION: int = 384  # Dimensión de los embeddings
    CHUNK_SIZE: int = 1000  # Tamaño aproximado de cada chunk en caracteres
    CHUNK_OVERLAP: int = 200  # Solapamiento entre chunks en caracteres
    MAX_RETRIES: int = 3  # Número máximo de reintentos para generación de embeddings
    RETRY_DELAY: int = 1  # Tiempo de espera entre reintentos en segundos
    
    # Configuración de límites de contexto
    MAX_CONTEXT_TOKENS: int = 4000  # Máximo número de tokens para el bloque de contexto
    CONTEXT_TOKEN_BUFFER: int = 100  # Buffer para evitar exceder límites estrictos
    CONTEXT_SEPARATOR: str = "\n\n---\n\n"  # Separador entre chunks en el bloque de contexto
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Anthropic (Claude)
    ANTHROPIC_API_KEY: str
    
    # AI Configuration
    DEFAULT_AI_TIMEOUT: int = 30  # segundos
    DEFAULT_AI_MAX_RETRIES: int = 3
    DEFAULT_AI_TEMPERATURE: float = 0.7
    DEFAULT_AI_MAX_TOKENS: int = 1000
    
    @property
    def sync_database_url(self) -> str:
        """URL de database síncrona para Alembic"""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL no está configurado")
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    @property
    def async_database_url(self) -> str:
        """URL de database asíncrona para SQLModel"""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL no está configurado")
        return self.DATABASE_URL

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Si no hay DATABASE_URL pero sí variables individuales, construirla
        if not self.DATABASE_URL and all([
            self.POSTGRES_SERVER, 
            self.POSTGRES_USER, 
            self.POSTGRES_PASSWORD, 
            self.POSTGRES_DB, 
            self.POSTGRES_PORT
        ]):
            self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
        # Si DATABASE_URL viene de Render (postgresql://), convertir a asyncpg
        elif self.DATABASE_URL and not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            if self.DATABASE_URL.startswith("postgresql://"):
                self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        
        # Configurar DEBUG basado en ENVIRONMENT
        if self.ENVIRONMENT == "production":
            self.DEBUG = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)


settings = Settings() 