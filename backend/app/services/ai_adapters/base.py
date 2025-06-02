from abc import ABC, abstractmethod
import time
from typing import Optional, Dict, Any, List
import httpx
import asyncio
import logging
from datetime import datetime, timedelta
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    retry_if_result
)

from app.schemas.ai_response import (
    AIRequest, StandardAIResponse, AIResponseStatus, AIProviderEnum,
    ErrorDetail, ErrorCategory, RetryInfo, ProviderHealthInfo, ProviderHealthStatus
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class BaseAIAdapter(ABC):
    """
    Clase base abstracta para todos los adaptadores de IA.
    Define la interfaz común que deben implementar todos los adaptadores.
    """
    
    def __init__(self, api_key: str, timeout: int = None, max_retries: int = None):
        self.api_key = api_key
        self.timeout = timeout or settings.DEFAULT_AI_TIMEOUT
        self.max_retries = max_retries or settings.DEFAULT_AI_MAX_RETRIES
        
        # Métricas y salud del proveedor
        self.health_info = ProviderHealthInfo(
            provider=self.provider_name,
            status=ProviderHealthStatus.UNKNOWN
        )
        self._request_history: List[Dict[str, Any]] = []
        
        # Cliente HTTP asíncrono
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers=self._get_default_headers()
        )
    
    @property
    @abstractmethod
    def provider_name(self) -> AIProviderEnum:
        """Nombre del proveedor de IA"""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """URL base de la API"""
        pass
    
    @abstractmethod
    def _get_default_headers(self) -> dict:
        """Headers por defecto para las solicitudes"""
        pass
    
    @abstractmethod
    def _build_payload(self, request: AIRequest) -> dict:
        """Construye el payload específico del proveedor"""
        pass
    
    @abstractmethod
    def _extract_response_text(self, response_data: dict) -> str:
        """Extrae el texto de respuesta del JSON del proveedor"""
        pass
    
    @abstractmethod
    def _extract_usage_info(self, response_data: dict) -> Optional[dict]:
        """Extrae información de uso (tokens, costos, etc.)"""
        pass
    
    def _classify_error(self, exception: Exception) -> ErrorDetail:
        """Clasifica el tipo de error para mejor manejo"""
        if isinstance(exception, httpx.TimeoutException):
            return ErrorDetail(
                category=ErrorCategory.NETWORK,
                code="TIMEOUT",
                message="Request timeout exceeded"
            )
        elif isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            
            if status_code == 401:
                return ErrorDetail(
                    category=ErrorCategory.AUTHENTICATION,
                    code="AUTH_ERROR",
                    message="Authentication failed - check API key"
                )
            elif status_code == 429:
                # Extraer retry-after header si existe
                retry_after = None
                if 'retry-after' in exception.response.headers:
                    try:
                        retry_after = int(exception.response.headers['retry-after'])
                    except ValueError:
                        pass
                
                return ErrorDetail(
                    category=ErrorCategory.RATE_LIMITING,
                    code="RATE_LIMIT",
                    message="Rate limit exceeded",
                    retry_after=retry_after
                )
            elif status_code == 402:
                return ErrorDetail(
                    category=ErrorCategory.QUOTA,
                    code="QUOTA_EXCEEDED", 
                    message="Quota exceeded - insufficient credits"
                )
            elif 500 <= status_code < 600:
                return ErrorDetail(
                    category=ErrorCategory.EXTERNAL_API,
                    code=f"SERVER_ERROR_{status_code}",
                    message=f"Server error: {status_code}"
                )
            else:
                return ErrorDetail(
                    category=ErrorCategory.EXTERNAL_API,
                    code=f"HTTP_{status_code}",
                    message=f"HTTP error: {status_code}"
                )
        elif isinstance(exception, httpx.NetworkError):
            return ErrorDetail(
                category=ErrorCategory.NETWORK,
                code="NETWORK_ERROR",
                message="Network connection failed"
            )
        else:
            return ErrorDetail(
                category=ErrorCategory.INTERNAL,
                code="UNKNOWN_ERROR",
                message=str(exception)
            )
    
    def _should_retry(self, error_detail: ErrorDetail) -> bool:
        """Determina si se debe reintentar basándose en el tipo de error"""
        non_retryable = {
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.QUOTA,
            ErrorCategory.VALIDATION
        }
        return error_detail.category not in non_retryable
    
    async def generate_response(self, request: AIRequest) -> StandardAIResponse:
        """
        Método principal para generar una respuesta.
        Implementa lógica robusta de reintentos y manejo de errores.
        """
        start_time = time.time()
        retry_info = RetryInfo(total_attempts=0, failed_attempts=[])
        
        for attempt in range(1, self.max_retries + 1):
            retry_info.total_attempts = attempt
            attempt_start = time.time()
            
            try:
                logger.info(f"Intento {attempt}/{self.max_retries} para {self.provider_name}")
                
                response = await self._make_api_call(request)
                
                # Calcular latencia total y del intento
                total_latency_ms = int((time.time() - start_time) * 1000)
                attempt_latency_ms = int((time.time() - attempt_start) * 1000)
                
                # Marcar intento exitoso
                retry_info.successful_attempt = attempt
                retry_info.total_retry_time_ms = total_latency_ms
                
                # Actualizar métricas de salud
                self._update_health_metrics(success=True, latency_ms=attempt_latency_ms)
                
                # Respuesta exitosa
                return StandardAIResponse(
                    ia_provider_name=self.provider_name,
                    response_text=self._extract_response_text(response),
                    status=AIResponseStatus.SUCCESS,
                    latency_ms=total_latency_ms,
                    retry_info=retry_info if attempt > 1 else None,
                    usage_info=self._extract_usage_info(response),
                    provider_metadata={"raw_response": response}
                )
                
            except Exception as e:
                attempt_latency_ms = int((time.time() - attempt_start) * 1000)
                error_detail = self._classify_error(e)
                
                # Registrar el intento fallido
                retry_info.failed_attempts.append(f"Attempt {attempt}: {error_detail.message}")
                
                logger.warning(f"Intento {attempt} falló para {self.provider_name}: {error_detail.message}")
                
                # Verificar si debemos reintentar
                if attempt == self.max_retries or not self._should_retry(error_detail):
                    # No más intentos o error no retryable
                    total_latency_ms = int((time.time() - start_time) * 1000)
                    retry_info.total_retry_time_ms = total_latency_ms
                    
                    # Actualizar métricas de salud
                    self._update_health_metrics(success=False, latency_ms=attempt_latency_ms)
                    
                    # Mapear status específico
                    status_mapping = {
                        ErrorCategory.NETWORK: AIResponseStatus.TIMEOUT,
                        ErrorCategory.RATE_LIMITING: AIResponseStatus.RATE_LIMIT,
                        ErrorCategory.AUTHENTICATION: AIResponseStatus.AUTH_ERROR,
                        ErrorCategory.QUOTA: AIResponseStatus.QUOTA_EXCEEDED,
                        ErrorCategory.EXTERNAL_API: AIResponseStatus.SERVICE_UNAVAILABLE
                    }
                    
                    status = status_mapping.get(error_detail.category, AIResponseStatus.ERROR)
                    
                    return StandardAIResponse(
                        ia_provider_name=self.provider_name,
                        status=status,
                        error_message=error_detail.message,
                        error_detail=error_detail,
                        latency_ms=total_latency_ms,
                        retry_info=retry_info
                    )
                
                # Esperar antes del siguiente intento (backoff exponencial)
                if attempt < self.max_retries:
                    wait_time = min(2 ** (attempt - 1), 30)  # Max 30 segundos
                    if error_detail.retry_after:
                        wait_time = max(wait_time, error_detail.retry_after)
                    
                    logger.info(f"Esperando {wait_time}s antes del siguiente intento")
                    await asyncio.sleep(wait_time)
        
        # Este punto no debería alcanzarse, pero por seguridad
        total_latency_ms = int((time.time() - start_time) * 1000)
        return StandardAIResponse(
            ia_provider_name=self.provider_name,
            status=AIResponseStatus.ERROR,
            error_message="Máximo número de intentos alcanzado",
            latency_ms=total_latency_ms,
            retry_info=retry_info
        )
    
    async def _make_api_call(self, request: AIRequest) -> dict:
        """Realiza la llamada API específica del proveedor"""
        payload = self._build_payload(request)
        
        response = await self.client.post(
            self.base_url,
            json=payload
        )
        
        response.raise_for_status()
        return response.json()
    
    def _update_health_metrics(self, success: bool, latency_ms: int):
        """Actualiza las métricas de salud del proveedor"""
        now = datetime.utcnow()
        
        # Agregar a historial
        self._request_history.append({
            'timestamp': now,
            'success': success,
            'latency_ms': latency_ms
        })
        
        # Limpiar historial antiguo (últimas 24 horas)
        cutoff = now - timedelta(hours=24)
        self._request_history = [
            req for req in self._request_history 
            if req['timestamp'] > cutoff
        ]
        
        # Actualizar métricas
        if success:
            self.health_info.last_successful_request = now
            self.health_info.consecutive_failures = 0
        else:
            self.health_info.last_failed_request = now
            self.health_info.consecutive_failures += 1
        
        # Calcular métricas de las últimas 24h
        if self._request_history:
            successful_requests = [req for req in self._request_history if req['success']]
            
            self.health_info.total_requests_24h = len(self._request_history)
            self.health_info.total_errors_24h = len(self._request_history) - len(successful_requests)
            self.health_info.success_rate_24h = len(successful_requests) / len(self._request_history)
            
            if successful_requests:
                self.health_info.avg_latency_ms = int(
                    sum(req['latency_ms'] for req in successful_requests) / len(successful_requests)
                )
        
        # Determinar estado de salud
        if self.health_info.consecutive_failures >= 5:
            self.health_info.status = ProviderHealthStatus.UNHEALTHY
        elif self.health_info.success_rate_24h is not None and self.health_info.success_rate_24h < 0.8:
            self.health_info.status = ProviderHealthStatus.DEGRADED
        else:
            self.health_info.status = ProviderHealthStatus.HEALTHY
    
    def get_health_info(self) -> ProviderHealthInfo:
        """Retorna información de salud actual del proveedor"""
        return self.health_info.model_copy()
    
    async def health_check(self) -> bool:
        """Realiza una verificación básica de salud"""
        try:
            # Hacer una solicitud simple para verificar conectividad
            test_request = AIRequest(
                prompt="Hello",
                max_tokens=1,
                temperature=0.1
            )
            response = await self.generate_response(test_request)
            return response.status == AIResponseStatus.SUCCESS
        except Exception as e:
            logger.error(f"Health check falló para {self.provider_name}: {e}")
            return False
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose() 