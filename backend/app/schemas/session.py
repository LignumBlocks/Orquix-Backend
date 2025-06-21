from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# Schemas para Session

class SessionBase(BaseModel):
    """Schema base para Session."""
    accumulated_context: str = Field(default="", description="Contexto acumulado de la sesión")
    final_question: Optional[str] = Field(None, description="Pregunta final de la sesión")
    status: str = Field(default="active", description="Estado de la sesión")


class SessionCreate(SessionBase):
    """Schema para crear una sesión."""
    chat_id: UUID = Field(..., description="ID del chat al que pertenece la sesión")


class SessionCreateRequest(SessionBase):
    """Schema para crear una sesión desde endpoint (sin chat_id)."""
    pass  # Solo hereda los campos base


class SessionUpdate(BaseModel):
    """Schema para actualizar una sesión."""
    accumulated_context: Optional[str] = Field(None, description="Nuevo contexto acumulado")
    final_question: Optional[str] = Field(None, description="Nueva pregunta final")
    status: Optional[str] = Field(None, description="Nuevo estado de la sesión")


class SessionResponse(SessionBase):
    """Schema para respuesta de sesión."""
    id: UUID = Field(..., description="ID único de la sesión")
    chat_id: UUID = Field(..., description="ID del chat")
    previous_session_id: Optional[UUID] = Field(None, description="ID de la sesión anterior")
    user_id: Optional[UUID] = Field(None, description="ID del usuario")
    order_index: int = Field(..., description="Índice de orden en el chat")
    started_at: datetime = Field(..., description="Fecha de inicio")
    finished_at: Optional[datetime] = Field(None, description="Fecha de finalización")
    deleted_at: Optional[datetime] = Field(None, description="Fecha de eliminación")

    class Config:
        from_attributes = True


class SessionSummary(BaseModel):
    """Schema resumido para listados de sesiones."""
    id: UUID = Field(..., description="ID único de la sesión")
    order_index: int = Field(..., description="Índice de orden")
    status: str = Field(..., description="Estado de la sesión")
    started_at: datetime = Field(..., description="Fecha de inicio")
    finished_at: Optional[datetime] = Field(None, description="Fecha de finalización")
    context_length: int = Field(default=0, description="Longitud del contexto acumulado")
    interactions_count: int = Field(default=0, description="Número de interacciones")
    has_final_question: bool = Field(default=False, description="Si tiene pregunta final")

    class Config:
        from_attributes = True


class SessionWithContext(SessionResponse):
    """Schema de sesión con contexto completo."""
    context_preview: str = Field(default="", description="Vista previa del contexto (primeros 200 chars)")
    context_word_count: int = Field(default=0, description="Número de palabras en el contexto")
    context_sections: List[str] = Field(default=[], description="Secciones identificadas en el contexto")

    class Config:
        from_attributes = True


class SessionWithInteractions(SessionResponse):
    """Schema de sesión con sus interacciones."""
    interactions: List[dict] = Field(default=[], description="Lista de interacciones")

    class Config:
        from_attributes = True


class SessionContextChain(BaseModel):
    """Schema para cadena de contexto de sesiones."""
    session_id: UUID = Field(..., description="ID de la sesión solicitada")
    context_chain: List[SessionResponse] = Field(..., description="Cadena de sesiones con contexto")
    total_context_length: int = Field(..., description="Longitud total del contexto acumulado")
    sessions_count: int = Field(..., description="Número de sesiones en la cadena")


class SessionStats(BaseModel):
    """Schema para estadísticas de una sesión."""
    session_id: UUID = Field(..., description="ID de la sesión")
    interactions_count: int = Field(..., description="Total de interacciones")
    context_length: int = Field(..., description="Longitud del contexto")
    context_word_count: int = Field(..., description="Número de palabras")
    processing_time_total: int = Field(..., description="Tiempo total de procesamiento (ms)")
    ai_responses_count: int = Field(..., description="Número de respuestas de IA")
    duration_minutes: Optional[float] = Field(None, description="Duración en minutos")


class SessionStatusUpdate(BaseModel):
    """Schema para actualizar solo el estado de una sesión."""
    status: str = Field(..., description="Nuevo estado")
    final_question: Optional[str] = Field(None, description="Pregunta final (si se completa)")


class SessionContextUpdate(BaseModel):
    """Schema para actualizar solo el contexto de una sesión."""
    accumulated_context: str = Field(..., description="Nuevo contexto acumulado")


# Schemas para respuestas de listado

class SessionListResponse(BaseModel):
    """Schema para respuesta de listado de sesiones."""
    sessions: List[SessionSummary] = Field(..., description="Lista de sesiones")
    total: int = Field(..., description="Total de sesiones")
    page: int = Field(..., description="Página actual")
    per_page: int = Field(..., description="Sesiones por página")
    has_next: bool = Field(..., description="Si hay más páginas")


class SessionsByStatusResponse(BaseModel):
    """Schema para sesiones agrupadas por estado."""
    active: List[SessionSummary] = Field(default=[], description="Sesiones activas")
    completed: List[SessionSummary] = Field(default=[], description="Sesiones completadas")
    archived: List[SessionSummary] = Field(default=[], description="Sesiones archivadas")
    total_by_status: dict = Field(default={}, description="Conteo por estado")


# Schemas para operaciones especiales

class SessionBulkUpdate(BaseModel):
    """Schema para actualización masiva de sesiones."""
    session_ids: List[UUID] = Field(..., description="IDs de las sesiones a actualizar")
    status: Optional[str] = Field(None, description="Nuevo estado para todas")
    archive: Optional[bool] = Field(None, description="Archivar/desarchivar todas")


class SessionMergeRequest(BaseModel):
    """Schema para fusionar sesiones."""
    source_session_ids: List[UUID] = Field(..., description="IDs de sesiones a fusionar")
    target_session_id: UUID = Field(..., description="ID de sesión destino")
    merge_strategy: str = Field(default="append", description="Estrategia de fusión: append, prepend, smart")


# Forward reference para evitar import circular
# InteractionEventResponse se importará dinámicamente cuando sea necesario 