from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class AIProviderEnum(str, Enum):
    """Proveedores de IA soportados"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class AIResponseStatus(str, Enum):
    """Estados posibles de una respuesta de IA"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"

class StandardAIResponse(BaseModel):
    """
    Respuesta normalizada de cualquier proveedor de IA.
    Todos los adaptadores deben retornar este formato.
    """
    ia_provider_name: AIProviderEnum
    response_text: Optional[str] = None
    status: AIResponseStatus
    error_message: Optional[str] = None
    latency_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadatos específicos del proveedor
    provider_metadata: Optional[Dict[str, Any]] = None
    
    # Información de uso (tokens, costos, etc.)
    usage_info: Optional[Dict[str, Any]] = None

class AIRequest(BaseModel):
    """Estructura estándar para solicitudes a IAs"""
    prompt: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    system_message: Optional[str] = None
    
    # Metadatos del contexto
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None 