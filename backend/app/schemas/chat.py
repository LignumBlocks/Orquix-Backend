from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# Schemas para Chat

class ChatBase(BaseModel):
    """Schema base para Chat."""
    title: str = Field(..., min_length=1, max_length=255, description="Título del chat")
    is_archived: bool = Field(default=False, description="Si el chat está archivado")


class ChatCreate(ChatBase):
    """Schema para crear un chat."""
    project_id: UUID = Field(..., description="ID del proyecto al que pertenece el chat")


class ChatCreateRequest(ChatBase):
    """Schema para crear un chat desde endpoint (sin project_id)."""
    pass  # Solo hereda title e is_archived


class ChatUpdate(BaseModel):
    """Schema para actualizar un chat."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Nuevo título del chat")
    is_archived: Optional[bool] = Field(None, description="Nuevo estado de archivado")


class ChatResponse(ChatBase):
    """Schema para respuesta de chat."""
    id: UUID = Field(..., description="ID único del chat")
    project_id: UUID = Field(..., description="ID del proyecto")
    user_id: Optional[UUID] = Field(None, description="ID del usuario propietario")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")
    deleted_at: Optional[datetime] = Field(None, description="Fecha de eliminación (si está eliminado)")

    class Config:
        from_attributes = True


class ChatSummary(BaseModel):
    """Schema resumido para listados de chats."""
    id: UUID = Field(..., description="ID único del chat")
    title: str = Field(..., description="Título del chat")
    is_archived: bool = Field(..., description="Si el chat está archivado")
    created_at: datetime = Field(..., description="Fecha de creación")
    sessions_count: int = Field(default=0, description="Número de sesiones en el chat")
    last_activity: Optional[datetime] = Field(None, description="Fecha de última actividad")

    class Config:
        from_attributes = True


class ChatWithSessions(ChatResponse):
    """Schema de chat con sus sesiones."""
    sessions: List[dict] = Field(default=[], description="Lista de sesiones del chat")

    class Config:
        from_attributes = True


class ChatStats(BaseModel):
    """Schema para estadísticas de un chat."""
    chat_id: UUID = Field(..., description="ID del chat")
    total_sessions: int = Field(..., description="Total de sesiones")
    active_sessions: int = Field(..., description="Sesiones activas")
    completed_sessions: int = Field(..., description="Sesiones completadas")
    total_interactions: int = Field(..., description="Total de interacciones")
    total_context_length: int = Field(..., description="Longitud total de contexto acumulado")
    first_session_date: Optional[datetime] = Field(None, description="Fecha de primera sesión")
    last_session_date: Optional[datetime] = Field(None, description="Fecha de última sesión")


# Schemas para respuestas de listado

class ChatListResponse(BaseModel):
    """Schema para respuesta de listado de chats."""
    chats: List[ChatSummary] = Field(..., description="Lista de chats")
    total: int = Field(..., description="Total de chats")
    page: int = Field(..., description="Página actual")
    per_page: int = Field(..., description="Chats por página")
    has_next: bool = Field(..., description="Si hay más páginas")


# Forward reference para evitar import circular
# SessionResponse se importará dinámicamente cuando sea necesario 