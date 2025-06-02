from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ServiceStatus(BaseModel):
    """Estado de un servicio específico"""
    name: str
    status: str  # "healthy", "unhealthy", "degraded", "unknown"
    response_time_ms: Optional[int] = None
    last_check: datetime
    error: Optional[str] = None


class DatabaseHealth(BaseModel):
    """Estado de la base de datos"""
    status: str
    connection_pool_size: Optional[int] = None
    active_connections: Optional[int] = None
    response_time_ms: Optional[int] = None


class AIProviderHealth(BaseModel):
    """Estado de los proveedores de IA"""
    openai: ServiceStatus
    anthropic: ServiceStatus


class SystemResources(BaseModel):
    """Recursos del sistema"""
    memory_usage_percent: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    disk_usage_percent: Optional[float] = None


class HealthResponse(BaseModel):
    """Respuesta completa del endpoint de salud"""
    status: str = Field(..., description="Estado general: healthy, unhealthy, degraded")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    uptime_seconds: int
    
    # Estados específicos
    database: DatabaseHealth
    ai_providers: AIProviderHealth
    system: Optional[SystemResources] = None
    
    # Métricas adicionales
    total_interactions_today: Optional[int] = None
    average_response_time_ms: Optional[float] = None
    error_rate_percent: Optional[float] = None


class SimpleHealthResponse(BaseModel):
    """Respuesta simple de salud para monitoreo básico"""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message: str = "Service is operational" 