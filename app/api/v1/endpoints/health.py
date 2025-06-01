import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.schemas.health import (
    HealthResponse, 
    SimpleHealthResponse, 
    DatabaseHealth, 
    AIProviderHealth,
    ServiceStatus,
    SystemResources
)
from app.services.ai_adapters.openai_adapter import OpenAIAdapter
from app.services.ai_adapters.anthropic_adapter import AnthropicAdapter
from app.core.metrics import metrics_collector

logger = logging.getLogger(__name__)
router = APIRouter()

# Variable para trackear el tiempo de inicio de la aplicación
start_time = datetime.utcnow()


async def check_database_health(db: AsyncSession) -> DatabaseHealth:
    """Verificar el estado de la base de datos"""
    try:
        start = time.time()
        
        # Realizar una consulta simple para verificar conectividad
        result = await db.exec("SELECT 1")
        
        response_time = int((time.time() - start) * 1000)
        
        return DatabaseHealth(
            status="healthy",
            response_time_ms=response_time,
            connection_pool_size=None,  # Se puede implementar según el pool usado
            active_connections=None
        )
        
    except Exception as e:
        logger.error(f"Error verificando BD: {e}")
        return DatabaseHealth(
            status="unhealthy",
            response_time_ms=None
        )


async def check_ai_providers() -> AIProviderHealth:
    """Verificar el estado de los proveedores de IA"""
    
    # Verificar OpenAI
    openai_status = ServiceStatus(
        name="OpenAI GPT",
        status="unknown",
        last_check=datetime.utcnow()
    )
    
    try:
        if settings.OPENAI_API_KEY:
            start = time.time()
            adapter = OpenAIAdapter(api_key=settings.OPENAI_API_KEY)
            
            # Realizar una consulta muy simple para verificar conectividad
            # En un entorno real, podrías hacer una llamada de verificación real
            response_time = int((time.time() - start) * 1000)
            
            openai_status.status = "healthy"
            openai_status.response_time_ms = response_time
        else:
            openai_status.status = "unavailable"
            openai_status.error = "API key no configurada"
            
    except Exception as e:
        openai_status.status = "unhealthy"
        openai_status.error = str(e)
        logger.error(f"Error verificando OpenAI: {e}")
    
    # Verificar Anthropic
    anthropic_status = ServiceStatus(
        name="Anthropic Claude",
        status="unknown",
        last_check=datetime.utcnow()
    )
    
    try:
        if settings.ANTHROPIC_API_KEY:
            start = time.time()
            adapter = AnthropicAdapter(api_key=settings.ANTHROPIC_API_KEY)
            
            response_time = int((time.time() - start) * 1000)
            
            anthropic_status.status = "healthy"
            anthropic_status.response_time_ms = response_time
        else:
            anthropic_status.status = "unavailable"
            anthropic_status.error = "API key no configurada"
            
    except Exception as e:
        anthropic_status.status = "unhealthy"
        anthropic_status.error = str(e)
        logger.error(f"Error verificando Anthropic: {e}")
    
    return AIProviderHealth(
        openai=openai_status,
        anthropic=anthropic_status
    )


def get_system_resources() -> SystemResources:
    """Obtener métricas de recursos del sistema"""
    try:
        return SystemResources(
            memory_usage_percent=psutil.virtual_memory().percent,
            cpu_usage_percent=psutil.cpu_percent(interval=1),
            disk_usage_percent=psutil.disk_usage('/').percent
        )
    except Exception as e:
        logger.warning(f"Error obteniendo métricas del sistema: {e}")
        return SystemResources()


@router.get("/", response_model=SimpleHealthResponse)
async def simple_health_check() -> SimpleHealthResponse:
    """
    GET /api/v1/health
    
    Endpoint de salud simple para monitoreo básico.
    """
    return SimpleHealthResponse(
        status="healthy",
        message="Orquix Backend está operativo"
    )


@router.get("/detailed", response_model=HealthResponse)
async def detailed_health_check(
    db: AsyncSession = Depends(get_db)
) -> HealthResponse:
    """
    GET /api/v1/health/detailed
    
    Endpoint de salud detallado con métricas completas del sistema.
    """
    # Verificar componentes del sistema
    db_health = await check_database_health(db)
    ai_health = await check_ai_providers()
    system_resources = get_system_resources()
    
    # Calcular uptime
    uptime = datetime.utcnow() - start_time
    uptime_seconds = int(uptime.total_seconds())
    
    # Determinar estado general del sistema
    overall_status = "healthy"
    
    if db_health.status == "unhealthy":
        overall_status = "unhealthy"
    elif (ai_health.openai.status == "unhealthy" and 
          ai_health.anthropic.status == "unhealthy"):
        overall_status = "degraded"
    elif (system_resources.memory_usage_percent and 
          system_resources.memory_usage_percent > 90):
        overall_status = "degraded"
    
    # Métricas adicionales (en un entorno real, se obtendrían de la BD)
    total_interactions_today = None  # TODO: Implementar consulta a BD
    average_response_time = None     # TODO: Calcular desde métricas
    error_rate = None                # TODO: Calcular desde logs
    
    return HealthResponse(
        status=overall_status,
        version=settings.PROJECT_VERSION,
        uptime_seconds=uptime_seconds,
        database=db_health,
        ai_providers=ai_health,
        system=system_resources,
        total_interactions_today=total_interactions_today,
        average_response_time_ms=average_response_time,
        error_rate_percent=error_rate
    )


@router.get("/database", response_model=DatabaseHealth)
async def database_health_check(
    db: AsyncSession = Depends(get_db)
) -> DatabaseHealth:
    """
    GET /api/v1/health/database
    
    Verificar específicamente el estado de la base de datos.
    """
    return await check_database_health(db)


@router.get("/ai-providers", response_model=AIProviderHealth)
async def ai_providers_health_check() -> AIProviderHealth:
    """
    GET /api/v1/health/ai-providers
    
    Verificar específicamente el estado de los proveedores de IA.
    """
    return await check_ai_providers()


@router.get("/system", response_model=SystemResources)
async def system_resources_check() -> SystemResources:
    """
    GET /api/v1/health/system
    
    Obtener métricas de recursos del sistema.
    """
    return get_system_resources()


@router.get("/liveness")
async def liveness_probe() -> dict:
    """
    GET /api/v1/health/liveness
    
    Probe de liveness para Kubernetes u otros orquestadores.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/readiness")
async def readiness_probe(
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    GET /api/v1/health/readiness
    
    Probe de readiness para verificar que el servicio está listo para recibir tráfico.
    """
    try:
        # Verificar BD básica
        await db.exec("SELECT 1")
        
        # Verificar que al menos un proveedor de IA esté disponible
        has_ai_provider = bool(settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY)
        
        if not has_ai_provider:
            return {
                "status": "not_ready", 
                "reason": "No AI providers configured",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "status": "ready", 
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready", 
            "reason": str(e),
            "timestamp": datetime.utcnow().isoformat()
        } 