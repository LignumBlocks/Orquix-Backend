from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from app.schemas.query import ContextInfo

from app.schemas.ai_response import StandardAIResponse
from app.services.ai_moderator import ModeratorResponse


class QueryRequest(BaseModel):
    """Solicitud de consulta principal"""
    user_prompt_text: str = Field(..., min_length=1, max_length=10000, description="Texto de la consulta del usuario")
    include_context: bool = Field(default=True, description="Si incluir contexto del proyecto")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Temperatura para generación")
    max_tokens: Optional[int] = Field(default=None, ge=100, le=4000, description="Máximo número de tokens")


class InteractionEventCreate(BaseModel):
    """Esquema para crear un nuevo evento de interacción"""
    id: UUID
    project_id: UUID
    user_id: UUID
    user_prompt: str
    ai_responses: List[Dict[str, Any]]  # JSON serializable
    moderator_synthesis: Dict[str, Any]  # JSON serializable
    context_used: bool = False
    context_preview: Optional[str] = None
    processing_time_ms: int
    created_at: datetime


class InteractionEvent(BaseModel):
    """Evento de interacción almacenado en la base de datos"""
    id: UUID
    project_id: UUID
    user_prompt: str
    ai_responses: List[StandardAIResponse]
    moderator_synthesis: Optional[Dict[str, Any]] = None
    created_at: datetime
    processing_time_ms: int
    
    class Config:
        from_attributes = True


class QueryResponse(BaseModel):
    """Respuesta completa de una consulta"""
    interaction_event_id: UUID = Field(..., description="ID único del evento de interacción")
    synthesis_text: str = Field(..., description="Texto sintetizado por el moderador")
    moderator_quality: str = Field(..., description="Calidad de la síntesis (high, medium, low, failed)")
    
    # Datos del meta-análisis v2.0
    key_themes: List[str] = Field(default_factory=list, description="Temas clave identificados")
    contradictions: List[str] = Field(default_factory=list, description="Contradicciones detectadas")
    consensus_areas: List[str] = Field(default_factory=list, description="Áreas de consenso")
    recommendations: List[str] = Field(default_factory=list, description="Recomendaciones del moderador")
    suggested_questions: List[str] = Field(default_factory=list, description="Preguntas sugeridas")
    research_areas: List[str] = Field(default_factory=list, description="Áreas de investigación")
    
    context_info: Optional[ContextInfo] = Field(default=None, description="Información del contexto utilizado")
    
    # Metadatos
    individual_responses: List[StandardAIResponse] = Field(..., description="Respuestas individuales de cada IA")
    processing_time_ms: int = Field(..., description="Tiempo total de procesamiento")
    created_at: datetime = Field(..., description="Timestamp de creación")
    fallback_used: bool = Field(..., description="Si se usó el fallback del moderador")


class InteractionSummary(BaseModel):
    """Resumen de una interacción para historial"""
    id: UUID
    user_prompt: str = Field(..., max_length=200, description="Resumen del prompt del usuario")
    synthesis_preview: str = Field(..., max_length=300, description="Preview de la síntesis")
    moderator_quality: str
    created_at: datetime
    processing_time_ms: int


class InteractionHistoryResponse(BaseModel):
    """Respuesta del historial de interacciones"""
    interactions: List[InteractionSummary]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class InteractionDetailResponse(BaseModel):
    """Respuesta detallada de una interacción específica"""
    interaction: InteractionEvent
    synthesis_details: Optional[ModeratorResponse] = None 