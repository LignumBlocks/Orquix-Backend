from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class FeedbackCreate(BaseModel):
    """Esquema para crear feedback"""
    reference_id: UUID = Field(..., description="ID de referencia (interaction_event_id, project_id, etc.)")
    reference_type: Literal["interaction", "project", "synthesis", "general"] = Field(..., description="Tipo de referencia")
    score: int = Field(..., ge=1, le=5, description="Puntuación del 1 al 5")
    comment: Optional[str] = Field(default=None, max_length=1000, description="Comentario opcional del usuario")
    category: Optional[Literal["helpful", "accurate", "fast", "easy_to_use", "other"]] = Field(default=None, description="Categoría del feedback")


class FeedbackResponse(BaseModel):
    """Respuesta de feedback creado"""
    id: UUID
    reference_id: UUID
    reference_type: str
    score: int
    comment: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    """Estadísticas de feedback"""
    total_feedbacks: int
    average_score: float
    score_distribution: dict[int, int]  # score -> count
    recent_feedbacks: list[FeedbackResponse]
    
    
class FeedbackListResponse(BaseModel):
    """Respuesta para listar feedbacks"""
    feedbacks: list[FeedbackResponse]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool 