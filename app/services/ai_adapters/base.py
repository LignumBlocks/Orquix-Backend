from abc import ABC, abstractmethod
import time
from typing import Optional
import httpx
import asyncio
import logging

from app.schemas.ai_response import AIRequest, StandardAIResponse, AIResponseStatus, AIProviderEnum
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
    
    async def generate_response(self, request: AIRequest) -> StandardAIResponse:
        """
        Método principal para generar una respuesta.
        Implementa lógica común de reintentos y manejo de errores.
        """
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                response = await self._make_api_call(request)
                latency_ms = int((time.time() - start_time) * 1000)
                
                return StandardAIResponse(
                    ia_provider_name=self.provider_name,
                    response_text=self._extract_response_text(response),
                    status=AIResponseStatus.SUCCESS,
                    latency_ms=latency_ms,
                    usage_info=self._extract_usage_info(response),
                    provider_metadata={"raw_response": response}
                )
                
            except httpx.TimeoutException:
                latency_ms = int((time.time() - start_time) * 1000)
                logger.warning(f"Timeout en {self.provider_name} (intento {attempt + 1})")
                
                if attempt == self.max_retries - 1:
                    return StandardAIResponse(
                        ia_provider_name=self.provider_name,
                        status=AIResponseStatus.TIMEOUT,
                        error_message=f"Timeout después de {self.max_retries} intentos",
                        latency_ms=latency_ms
                    )
                    
            except httpx.HTTPStatusError as e:
                latency_ms = int((time.time() - start_time) * 1000)
                
                if e.response.status_code == 429:  # Rate limit
                    logger.warning(f"Rate limit en {self.provider_name} (intento {attempt + 1})")
                    
                    if attempt == self.max_retries - 1:
                        return StandardAIResponse(
                            ia_provider_name=self.provider_name,
                            status=AIResponseStatus.RATE_LIMIT,
                            error_message="Rate limit excedido",
                            latency_ms=latency_ms
                        )
                    
                    # Esperar antes del siguiente intento
                    await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                    continue
                
                # Otros errores HTTP
                return StandardAIResponse(
                    ia_provider_name=self.provider_name,
                    status=AIResponseStatus.ERROR,
                    error_message=f"HTTP {e.response.status_code}: {e.response.text}",
                    latency_ms=latency_ms
                )
                
            except Exception as e:
                latency_ms = int((time.time() - start_time) * 1000)
                logger.error(f"Error inesperado en {self.provider_name}: {str(e)}")
                
                return StandardAIResponse(
                    ia_provider_name=self.provider_name,
                    status=AIResponseStatus.ERROR,
                    error_message=f"Error inesperado: {str(e)}",
                    latency_ms=latency_ms
                )
        
        # Si llegamos aquí, todos los intentos fallaron
        latency_ms = int((time.time() - start_time) * 1000)
        return StandardAIResponse(
            ia_provider_name=self.provider_name,
            status=AIResponseStatus.ERROR,
            error_message=f"Falló después de {self.max_retries} intentos",
            latency_ms=latency_ms
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
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose() 