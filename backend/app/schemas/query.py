from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from app.schemas.ai_response import StandardAIResponse, AIProviderEnum

class QueryType(str, Enum):
    """Tipos de consulta soportados"""
    SIMPLE = "simple"  # Solo pregunta, sin contexto
    CONTEXT_AWARE = "context_aware"  # Pregunta + búsqueda de contexto
    FOLLOW_UP = "follow_up"  # Pregunta de seguimiento

class ContextConfig(BaseModel):
    """Configuración para la búsqueda de contexto"""
    top_k: int = 5
    similarity_threshold: Optional[float] = 0.7
    max_context_length: int = 3000
    include_metadata: bool = True

class QueryRequest(BaseModel):
    """Solicitud de consulta del usuario"""
    # Información básica
    user_question: str
    project_id: UUID
    user_id: Optional[UUID] = None
    
    # Configuración de la consulta
    query_type: QueryType = QueryType.CONTEXT_AWARE
    context_config: Optional[ContextConfig] = None
    
    # Selección de IAs
    ai_providers: Optional[List[AIProviderEnum]] = None  # Si None, usar todas disponibles
    
    # Configuración de IAs
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1200
    
    # Metadatos adicionales
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None

class ContextInfo(BaseModel):
    """Información sobre el contexto encontrado"""
    total_chunks: int
    avg_similarity: float
    sources_used: List[str]
    total_characters: int
    context_text: str

class QueryResponse(BaseModel):
    """Respuesta completa a una consulta"""
    # Información de la consulta
    query_id: str = Field(default_factory=lambda: str(uuid4()))
    original_question: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Contexto utilizado
    context_info: Optional[ContextInfo] = None
    
    # Respuestas de las IAs
    ai_responses: List[StandardAIResponse]
    
    # Respuesta seleccionada/moderada
    selected_response: Optional[StandardAIResponse] = None
    
    # Metadatos de la consulta
    processing_time_ms: int
    providers_used: List[AIProviderEnum]
    
    # Información adicional
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PromptTemplate(BaseModel):
    """Template para construcción de prompts"""
    system_template: str
    user_template: str
    context_template: str
    
    # Variables disponibles para interpolación
    available_variables: List[str] = [
        "user_question", 
        "context", 
        "project_name", 
        "user_name",
        "timestamp"
    ] 