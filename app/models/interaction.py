from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlmodel import SQLModel, Field, Column, String, Text, Integer, Boolean, DateTime, Relationship
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
        foreign_key="projects.id",
        index=True,
        description="ID del proyecto al que pertenece la interacción"
    )
    
    user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        description="ID del usuario que realizó la consulta"
    )
    
    # Datos de la consulta del esquema MVP
    user_prompt_text: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Prompt original del usuario"
    )
    
    context_used_summary: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Resumen del contexto utilizado en la consulta"
    )
    
    moderated_synthesis_id: Optional[UUID] = Field(
        default=None,
        foreign_key="moderated_syntheses.id",
        description="ID de la síntesis moderada (si existe)"
    )
    
    user_feedback_score: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="Puntuación de feedback del usuario (1-5)"
    )
    
    user_feedback_comment: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Comentario de feedback del usuario"
    )
    
    # Timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        description="Timestamp de creación de la interacción"
    )
    
    # Campos adicionales para compatibilidad con implementación actual
    ai_responses_json: Optional[str] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Respuestas de los proveedores de IA en formato JSON (backup)"
    )
    
    moderator_synthesis_json: Optional[str] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
        description="Síntesis y meta-análisis del moderador en formato JSON (backup)"
    )
    
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
    
    processing_time_ms: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="Tiempo total de procesamiento en milisegundos"
    )
    
    # Relationships según esquema MVP
    project: "Project" = Relationship(back_populates="interaction_events")
    user: "User" = Relationship(back_populates="interaction_events")
    ia_responses: List["IAResponse"] = Relationship(back_populates="interaction_event")
    moderated_synthesis: Optional["ModeratedSynthesis"] = Relationship()
    
    # Configuración del modelo
    class Config:
        table = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "project_id": "550e8400-e29b-41d4-a716-446655440001",
                "user_id": "550e8400-e29b-41d4-a716-446655440002",
                "user_prompt_text": "¿Cómo funciona la inteligencia artificial?",
                "context_used_summary": "Información sobre algoritmos de ML...",
                "user_feedback_score": 5,
                "user_feedback_comment": "Excelente respuesta",
                "created_at": "2024-01-15T10:30:00Z"
            }
        } 