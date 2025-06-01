from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel, Field, Column, String, Text, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB


class InteractionEvent(SQLModel, table=True):
    """
    Modelo de base de datos para eventos de interacción.
    Almacena todas las interacciones de usuarios con el sistema de IA.
    """
    __tablename__ = "interaction_events"
    
    # Identificadores
    id: UUID = Field(
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True, nullable=False),
        description="ID único del evento de interacción"
    )
    
    project_id: UUID = Field(
        sa_column=Column(PostgresUUID(as_uuid=True), nullable=False, index=True),
        description="ID del proyecto al que pertenece la interacción"
    )
    
    user_id: UUID = Field(
        sa_column=Column(PostgresUUID(as_uuid=True), nullable=False, index=True),
        description="ID del usuario que realizó la consulta"
    )
    
    # Datos de la consulta
    user_prompt: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Prompt original del usuario"
    )
    
    # Respuestas de IA (JSON)
    ai_responses_json: str = Field(
        sa_column=Column(JSONB, nullable=False),
        description="Respuestas de los proveedores de IA en formato JSON"
    )
    
    # Síntesis del moderador (JSON)
    moderator_synthesis_json: Optional[str] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Síntesis y meta-análisis del moderador en formato JSON"
    )
    
    # Contexto utilizado
    context_used: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False),
        description="Si se utilizó contexto del proyecto en la consulta"
    )
    
    context_preview: Optional[str] = Field(
        default=None,
        sa_column=Column(String(500), nullable=True),
        description="Preview del contexto utilizado (max 500 chars)"
    )
    
    # Métricas
    processing_time_ms: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="Tiempo total de procesamiento en milisegundos"
    )
    
    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        description="Timestamp de creación de la interacción"
    )
    
    # Configuración del modelo
    class Config:
        table = True
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "project_id": "550e8400-e29b-41d4-a716-446655440001",
                "user_id": "550e8400-e29b-41d4-a716-446655440002",
                "user_prompt": "¿Cómo funciona la inteligencia artificial?",
                "ai_responses_json": "[{\"provider\": \"openai\", \"response\": \"La IA...\"}]",
                "moderator_synthesis_json": "{\"synthesis_text\": \"La inteligencia artificial...\", \"quality\": \"high\"}",
                "context_used": True,
                "context_preview": "Contexto sobre IA...",
                "processing_time_ms": 2500,
                "created_at": "2024-01-15T10:30:00Z"
            }
        } 