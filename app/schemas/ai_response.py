from typing import Optional, Dict, Any, List
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
    AUTH_ERROR = "auth_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    SERVICE_UNAVAILABLE = "service_unavailable"

class ErrorCategory(str, Enum):
    """Categorías de errores para mejor clasificación"""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    RATE_LIMITING = "rate_limiting"
    QUOTA = "quota"
    VALIDATION = "validation"
    INTERNAL = "internal"
    EXTERNAL_API = "external_api"

class ErrorDetail(BaseModel):
    """Detalle específico de un error"""
    category: ErrorCategory
    code: Optional[str] = None
    message: str
    retry_after: Optional[int] = None  # Segundos hasta poder reintentar
    details: Optional[Dict[str, Any]] = None

class RetryInfo(BaseModel):
    """Información sobre reintentos realizados"""
    total_attempts: int
    successful_attempt: Optional[int] = None  # En qué intento fue exitoso
    failed_attempts: List[str] = []  # Errores de cada intento fallido
    total_retry_time_ms: int = 0

class StandardAIResponse(BaseModel):
    """
    Respuesta normalizada de cualquier proveedor de IA.
    Todos los adaptadores deben retornar este formato.
    """
    ia_provider_name: AIProviderEnum
    response_text: Optional[str] = None
    status: AIResponseStatus
    error_message: Optional[str] = None
    error_detail: Optional[ErrorDetail] = None
    latency_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Información de reintentos
    retry_info: Optional[RetryInfo] = None
    
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

class ProviderHealthStatus(str, Enum):
    """Estado de salud de un proveedor"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class ProviderHealthInfo(BaseModel):
    """Información de salud de un proveedor"""
    provider: AIProviderEnum
    status: ProviderHealthStatus
    last_successful_request: Optional[datetime] = None
    last_failed_request: Optional[datetime] = None
    success_rate_24h: Optional[float] = None  # 0.0 - 1.0
    avg_latency_ms: Optional[int] = None
    total_requests_24h: int = 0
    total_errors_24h: int = 0
    consecutive_failures: int = 0
    details: Optional[Dict[str, Any]] = None

class SystemHealthReport(BaseModel):
    """Reporte de salud del sistema completo"""
    overall_status: ProviderHealthStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    providers: List[ProviderHealthInfo]
    summary: Dict[str, Any] = Field(default_factory=dict) 