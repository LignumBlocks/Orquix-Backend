import time
import logging
from typing import Dict, Tuple, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitStore:
    """
    Almacén en memoria para tracking de rate limiting.
    En producción, se usaría Redis u otro store distribuido.
    """
    
    def __init__(self):
        # {client_id: [(timestamp, endpoint), ...]}
        self.requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        # {client_id: blocked_until_timestamp}
        self.blocked_until: Dict[str, float] = {}
        self.last_cleanup = time.time()
    
    def cleanup_old_requests(self, max_age_seconds: int = 3600):
        """Limpiar requests antiguos para evitar memory leaks"""
        current_time = time.time()
        
        # Solo limpiar cada 10 minutos
        if current_time - self.last_cleanup < 600:
            return
        
        cutoff_time = current_time - max_age_seconds
        
        for client_id in list(self.requests.keys()):
            client_requests = self.requests[client_id]
            
            # Remover requests antiguos
            while client_requests and client_requests[0][0] < cutoff_time:
                client_requests.popleft()
            
            # Si no quedan requests, remover el cliente
            if not client_requests:
                del self.requests[client_id]
        
        # Limpiar bloqueos expirados
        expired_blocks = [
            client_id for client_id, until_time in self.blocked_until.items()
            if until_time < current_time
        ]
        for client_id in expired_blocks:
            del self.blocked_until[client_id]
        
        self.last_cleanup = current_time
        logger.debug(f"Rate limit cleanup: {len(expired_blocks)} blocks expired")
    
    def is_blocked(self, client_id: str) -> bool:
        """Verificar si un cliente está bloqueado"""
        if client_id not in self.blocked_until:
            return False
        
        if time.time() >= self.blocked_until[client_id]:
            # El bloqueo expiró
            del self.blocked_until[client_id]
            return False
        
        return True
    
    def block_client(self, client_id: str, duration_seconds: int):
        """Bloquear un cliente por duración específica"""
        self.blocked_until[client_id] = time.time() + duration_seconds
        logger.warning(f"Cliente {client_id} bloqueado por {duration_seconds} segundos")
    
    def add_request(self, client_id: str, endpoint: str) -> int:
        """
        Agregar una nueva request y retornar el número de requests recientes
        """
        current_time = time.time()
        self.requests[client_id].append((current_time, endpoint))
        return len(self.requests[client_id])
    
    def count_recent_requests(
        self, 
        client_id: str, 
        window_seconds: int,
        endpoint_filter: Optional[str] = None
    ) -> int:
        """Contar requests recientes dentro de una ventana de tiempo"""
        if client_id not in self.requests:
            return 0
        
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        count = 0
        for timestamp, endpoint in self.requests[client_id]:
            if timestamp >= cutoff_time:
                if endpoint_filter is None or endpoint == endpoint_filter:
                    count += 1
        
        return count


# Instancia global del store (en producción usar Redis)
rate_limit_store = RateLimitStore()


class RateLimitConfig:
    """Configuración de rate limiting por endpoint"""
    
    # Rate limits por endpoint (requests por minuto)
    LIMITS = {
        # Endpoints de consulta más restrictivos
        "/api/v1/projects/{project_id}/query": {"requests": 30, "window": 60, "block_duration": 300},
        
        # Endpoints de autenticación
        "/api/v1/auth/session": {"requests": 60, "window": 60, "block_duration": 60},
        "/api/v1/auth/signout": {"requests": 10, "window": 60, "block_duration": 30},
        
        # Endpoints de proyectos
        "/api/v1/projects": {"requests": 100, "window": 60, "block_duration": 60},
        
        # Feedback más permisivo
        "/api/v1/feedback": {"requests": 50, "window": 60, "block_duration": 60},
        
        # Health checks muy permisivos
        "/api/v1/health": {"requests": 300, "window": 60, "block_duration": 30},
        
        # Límite global por IP
        "*": {"requests": 200, "window": 60, "block_duration": 120}
    }
    
    @classmethod
    def get_limit_for_endpoint(cls, path: str) -> Dict[str, int]:
        """Obtener configuración de límite para un endpoint específico"""
        
        # Buscar coincidencia exacta
        if path in cls.LIMITS:
            return cls.LIMITS[path]
        
        # Buscar coincidencias con parámetros de ruta
        for pattern, config in cls.LIMITS.items():
            if pattern != "*" and cls._path_matches_pattern(path, pattern):
                return config
        
        # Usar límite global por defecto
        return cls.LIMITS["*"]
    
    @staticmethod
    def _path_matches_pattern(path: str, pattern: str) -> bool:
        """Verificar si un path coincide con un patrón que contiene {param}"""
        import re
        
        # Convertir patrón de FastAPI a regex
        regex_pattern = re.sub(r'\{[^}]+\}', r'[^/]+', pattern)
        regex_pattern = f"^{regex_pattern}$"
        
        return bool(re.match(regex_pattern, path))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting para FastAPI
    """
    
    async def dispatch(self, request: Request, call_next):
        # Cleanup periódico
        rate_limit_store.cleanup_old_requests()
        
        # Obtener identificador del cliente
        client_id = self._get_client_id(request)
        
        # Verificar si está bloqueado
        if rate_limit_store.is_blocked(client_id):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Demasiadas solicitudes. Cliente temporalmente bloqueado.",
                    "retry_after": 300
                },
                headers={"Retry-After": "300"}
            )
        
        # Obtener configuración de límite para este endpoint
        endpoint_path = request.url.path
        limit_config = RateLimitConfig.get_limit_for_endpoint(endpoint_path)
        
        # Contar requests recientes para este endpoint específico
        recent_requests = rate_limit_store.count_recent_requests(
            client_id=client_id,
            window_seconds=limit_config["window"],
            endpoint_filter=endpoint_path
        )
        
        # Contar requests globales
        global_requests = rate_limit_store.count_recent_requests(
            client_id=client_id,
            window_seconds=RateLimitConfig.LIMITS["*"]["window"]
        )
        
        # Verificar límites
        if recent_requests >= limit_config["requests"]:
            # Bloquear cliente por comportamiento abusivo en endpoint específico
            rate_limit_store.block_client(
                client_id=client_id,
                duration_seconds=limit_config["block_duration"]
            )
            
            logger.warning(
                f"Rate limit exceeded para {client_id} en {endpoint_path}: "
                f"{recent_requests}/{limit_config['requests']}"
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Límite de {limit_config['requests']} requests por {limit_config['window']}s excedido para este endpoint",
                    "retry_after": limit_config["block_duration"]
                },
                headers={"Retry-After": str(limit_config["block_duration"])}
            )
        
        if global_requests >= RateLimitConfig.LIMITS["*"]["requests"]:
            # Bloquear por límite global
            rate_limit_store.block_client(
                client_id=client_id,
                duration_seconds=RateLimitConfig.LIMITS["*"]["block_duration"]
            )
            
            logger.warning(
                f"Global rate limit exceeded para {client_id}: "
                f"{global_requests}/{RateLimitConfig.LIMITS['*']['requests']}"
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Global rate limit exceeded",
                    "message": f"Límite global de {RateLimitConfig.LIMITS['*']['requests']} requests por minuto excedido",
                    "retry_after": RateLimitConfig.LIMITS["*"]["block_duration"]
                },
                headers={"Retry-After": str(RateLimitConfig.LIMITS["*"]["block_duration"])}
            )
        
        # Registrar la request
        rate_limit_store.add_request(client_id, endpoint_path)
        
        # Procesar la request normalmente
        response = await call_next(request)
        
        # Agregar headers informativos
        remaining = max(0, limit_config["requests"] - recent_requests - 1)
        response.headers["X-RateLimit-Limit"] = str(limit_config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + limit_config["window"]))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """
        Obtener identificador único del cliente.
        En producción, considerar usar usuario autenticado cuando esté disponible.
        """
        # Priorizar IP real del cliente (considerando proxies)
        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
            request.headers.get("x-real-ip") or
            request.client.host if request.client else "unknown"
        )
        
        # En el futuro, se puede agregar user_id para usuarios autenticados
        # para límites más granulares por usuario
        
        return f"ip:{client_ip}"


# Helper function para uso manual en endpoints específicos
async def check_rate_limit(request: Request, custom_limit: int, window_seconds: int = 60) -> bool:
    """
    Función helper para verificar rate limit manualmente en endpoints específicos
    
    Args:
        request: Request de FastAPI
        custom_limit: Límite personalizado de requests
        window_seconds: Ventana de tiempo en segundos
    
    Returns:
        True si está dentro del límite, False si excede
    """
    client_id = f"ip:{request.client.host if request.client else 'unknown'}"
    
    recent_requests = rate_limit_store.count_recent_requests(
        client_id=client_id,
        window_seconds=window_seconds,
        endpoint_filter=request.url.path
    )
    
    if recent_requests >= custom_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {recent_requests}/{custom_limit} requests in {window_seconds}s"
        )
    
    rate_limit_store.add_request(client_id, request.url.path)
    return True 