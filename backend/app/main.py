from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importar endpoints
from app.api.v1.endpoints import projects, auth, feedback, health, interactions, pre_analyst, context_chat, chats
from app.api.v1.context import router as context_router

# Configuración y middleware
from app.core.config import settings
from app.core.database import create_db_and_tables
from app.middleware.rate_limiting import RateLimitMiddleware

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de inicio y cierre de la aplicación"""
    # Startup
    logger.info("🚀 Iniciando Orquix Backend...")
    await create_db_and_tables()
    logger.info("✅ Base de datos inicializada")
    
    yield
    
    # Shutdown
    logger.info("🔄 Cerrando Orquix Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="""
    **Orquix Backend API** - Sistema de IA con Moderador Inteligente

    API completa para interactuar con múltiples proveedores de IA y obtener síntesis 
    inteligentes a través del Moderador v2.0 con meta-análisis profesional.

    ## Características principales:
    - 🧠 **Moderador IA v2.0**: Meta-análisis profesional de respuestas múltiples
    - 🔐 **Autenticación JWT**: Integración con NextAuth.js
    - 📊 **Proyectos**: Gestión completa de proyectos de investigación
    - 🔄 **Orquestación**: Consultas automáticas a múltiples IAs
    - 📈 **Historial**: Tracking completo de interacciones
    - 💬 **Feedback**: Sistema de retroalimentación de usuarios
    - ⚡ **Rate Limiting**: Protección contra abuso
    - 🏥 **Health Checks**: Monitoreo completo del sistema

    ## Integraciones:
    - **OpenAI GPT**: GPT-4, GPT-3.5-Turbo
    - **Anthropic Claude**: Claude-3 Sonnet, Claude-3 Haiku
    - **NextAuth.js**: Autenticación seamless
    - **PostgreSQL**: Base de datos principal
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ========================================
# CONFIGURACIÓN DE CORS
# ========================================

# Dominios permitidos en desarrollo y producción
allowed_origins = [
    "http://localhost:3000",  # Frontend Next.js en desarrollo
    "http://127.0.0.1:3000",
    "https://orquix.com",     # Dominio de producción (ajustar según necesidad)
    "https://app.orquix.com", # Subdominio de la app
    "https://orquix-frontend.onrender.com", # Frontend en Render Static Site
]

# En desarrollo, permitir más dominios
if settings.ENVIRONMENT == "development":
    allowed_origins.extend([
        "http://localhost:3001",
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Vite dev server alternativo
        "http://localhost:5175",  # Vite dev server puerto adicional
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175", # Vite dev server puerto adicional
        "http://localhost:8080",
        "http://localhost:8000",
    ])

# En producción, ser más permisivo con Render
logger.info(f"🌍 CORS Configuration - Environment: {settings.ENVIRONMENT}")
logger.info(f"🌍 CORS Configuration - Allowed origins: {allowed_origins}")

if settings.ENVIRONMENT == "production":
    # Permitir todos los orígenes temporalmente para debug de CORS
    allowed_origins = ["*"]
    allow_credentials = False  # No se puede usar credentials con "*"
    logger.info("🌍 CORS: Permitiendo todos los orígenes en producción (temporal)")
else:
    allow_credentials = True
    logger.info(f"🌍 CORS: Orígenes específicos en desarrollo: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
        "X-API-Key",
    ],
    expose_headers=[
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining", 
        "X-RateLimit-Reset",
    ],
    max_age=86400,  # Cache preflight por 24 horas
)

# ========================================
# MIDDLEWARE DE RATE LIMITING
# ========================================

# Solo aplicar rate limiting en producción y staging
if settings.ENVIRONMENT in ["production", "staging"]:
    app.add_middleware(RateLimitMiddleware)
    logger.info("✅ Rate limiting habilitado")
else:
    logger.info("⚠️ Rate limiting deshabilitado en desarrollo")

# ========================================
# ROUTERS / ENDPOINTS
# ========================================

# Endpoints de autenticación
app.include_router(
    auth.router, 
    prefix=f"{settings.API_V1_STR}/auth", 
    tags=["🔐 Autenticación"],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Sin permisos"},
    }
)

# Endpoints de proyectos (incluye consulta principal)
app.include_router(
    projects.router, 
    prefix=f"{settings.API_V1_STR}/projects", 
    tags=["📁 Proyectos"],
    dependencies=[],  # Las dependencias de auth están en cada endpoint
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Sin permisos"},
        404: {"description": "Proyecto no encontrado"},
    }
)

# Endpoints de interacciones/historial  
app.include_router(
    interactions.router, 
    prefix=f"{settings.API_V1_STR}/projects", 
    tags=["📜 Historial"],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Sin permisos"},
        404: {"description": "Interacción no encontrada"},
    }
)

# Endpoints de feedback
app.include_router(
    feedback.router, 
    prefix=f"{settings.API_V1_STR}/feedback", 
    tags=["💬 Feedback"],
    responses={
        401: {"description": "No autenticado"},
        400: {"description": "Datos inválidos"},
    }
)

# Endpoints de salud (sin autenticación para monitoreo)
app.include_router(
    health.router, 
    prefix=f"{settings.API_V1_STR}/health", 
    tags=["🏥 Salud del Sistema"]
)

# Endpoints de contexto (heredado)
app.include_router(
    context_router, 
    prefix=f"{settings.API_V1_STR}", 
    tags=["📄 Contexto"],
    responses={
        401: {"description": "No autenticado"},
    }
)

# Endpoints de Chat + Session (nueva arquitectura)
app.include_router(
    chats.router, 
    prefix=f"{settings.API_V1_STR}", 
    tags=["💬 Chats y Sesiones"],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Sin permisos"},
        404: {"description": "Chat o sesión no encontrada"},
    }
)

# Endpoints de PreAnalyst (análisis previo de consultas)
app.include_router(
    pre_analyst.router, 
    prefix=f"{settings.API_V1_STR}/pre-analyst", 
    tags=["🧠 PreAnalyst"],
    responses={
        400: {"description": "Datos inválidos"},
        500: {"description": "Error interno del servidor"},
    }
)

# Endpoints de contexto (nuevo)
app.include_router(
    context_chat.router, 
    prefix=f"{settings.API_V1_STR}/context-chat", 
    tags=["📄 Contexto Chat"],
    responses={
        401: {"description": "No autenticado"},
    }
)

# ========================================
# ENDPOINTS RAÍZ Y UTILIDADES
# ========================================

@app.get("/", tags=["🏠 Inicio"])
async def root():
    """Endpoint raíz con información del API"""
    return {
        "message": "¡Bienvenido a Orquix Backend API!",
        "version": settings.PROJECT_VERSION,
        "description": "Sistema de IA con Moderador Inteligente v2.0",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": f"{settings.API_V1_STR}/health",
        "features": [
            "🧠 Moderador IA v2.0 con meta-análisis profesional",
            "🔐 Autenticación JWT con NextAuth.js",
            "📊 Gestión completa de proyectos",
            "🔄 Orquestación multi-IA automática",
            "📈 Historial detallado de interacciones",
            "💬 Sistema de feedback de usuarios",
            "⚡ Rate limiting inteligente",
            "🏥 Health checks comprehensivos"
        ]
    }


@app.get("/api", tags=["ℹ️ Info API"])
async def api_info():
    """Información de la API y endpoints disponibles"""
    return {
        "api_version": "v1",
        "base_url": settings.API_V1_STR,
        "endpoints": {
            "auth": f"{settings.API_V1_STR}/auth",
            "projects": f"{settings.API_V1_STR}/projects",
            "feedback": f"{settings.API_V1_STR}/feedback", 
            "health": f"{settings.API_V1_STR}/health",
            "context": f"{settings.API_V1_STR}/context",
        },
        "features": {
            "authentication": "JWT con NextAuth.js",
            "rate_limiting": settings.ENVIRONMENT in ["production", "staging"],
            "cors_enabled": True,
            "moderator_version": "2.0",
            "ai_providers": ["OpenAI", "Anthropic"]
        }
    }


@app.get("/api/status", tags=["📊 Estado"])
async def api_status():
    """Estado rápido del API"""
    return {
        "status": "operational",
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime": "healthy",
        "services": {
            "api": "healthy",
            "database": "unknown",  # Se podría verificar aquí
            "ai_providers": "unknown"
        }
    }


# ========================================
# EVENTOS DE APLICACIÓN
# ========================================

@app.on_event("startup")
async def startup_event():
    """Evento adicional de startup para logging"""
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    logger.info(f"🌍 Entorno: {settings.ENVIRONMENT}")
    logger.info(f"🔗 API Base: {settings.API_V1_STR}")
    logger.info(f"📚 Documentación: /docs")
    logger.info(f"🏥 Health Check: {settings.API_V1_STR}/health")
    
    # Verificar configuración de IAs
    ai_providers = []
    if settings.OPENAI_API_KEY:
        ai_providers.append("OpenAI")
    if settings.ANTHROPIC_API_KEY:
        ai_providers.append("Anthropic")
    
    logger.info(f"🤖 Proveedores IA: {', '.join(ai_providers) if ai_providers else 'Ninguno configurado'}")
    logger.info(f"🛡️ Rate Limiting: {'Habilitado' if settings.ENVIRONMENT in ['production', 'staging'] else 'Deshabilitado'}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    ) 