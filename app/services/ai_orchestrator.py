from typing import List, Optional, Dict, Any
import asyncio
import logging
from enum import Enum

from app.services.ai_adapters.openai_adapter import OpenAIAdapter
from app.services.ai_adapters.anthropic_adapter import AnthropicAdapter
from app.schemas.ai_response import AIRequest, StandardAIResponse, AIProviderEnum, AIResponseStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIOrchestrationStrategy(str, Enum):
    """Estrategias de orquestación de IAs"""
    SINGLE = "single"  # Una sola IA
    PARALLEL = "parallel"  # Todas las IAs en paralelo
    FALLBACK = "fallback"  # Intentar una, si falla usar la siguiente
    FASTEST = "fastest"  # La primera que responda exitosamente

class AIOrchestrator:
    """
    Orquestador principal que gestiona múltiples IAs.
    Implementa diferentes estrategias de orquestación.
    """
    
    def __init__(self):
        self.adapters: Dict[AIProviderEnum, Any] = {}
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """Inicializa todos los adaptadores disponibles"""
        try:
            # OpenAI GPT-4o-mini
            if settings.OPENAI_API_KEY:
                self.adapters[AIProviderEnum.OPENAI] = OpenAIAdapter(
                    api_key=settings.OPENAI_API_KEY,
                    model="gpt-4o-mini"
                )
                logger.info("Adaptador OpenAI inicializado")
        except Exception as e:
            logger.error(f"Error inicializando adaptador OpenAI: {e}")
        
        try:
            # Anthropic Claude 3 Haiku
            if settings.ANTHROPIC_API_KEY:
                self.adapters[AIProviderEnum.ANTHROPIC] = AnthropicAdapter(
                    api_key=settings.ANTHROPIC_API_KEY,
                    model="claude-3-haiku-20240307"
                )
                logger.info("Adaptador Anthropic inicializado")
        except Exception as e:
            logger.error(f"Error inicializando adaptador Anthropic: {e}")
        
        if not self.adapters:
            logger.warning("No se inicializó ningún adaptador de IA")
    
    def get_available_providers(self) -> List[AIProviderEnum]:
        """Retorna lista de proveedores disponibles"""
        return list(self.adapters.keys())
    
    async def generate_single_response(
        self, 
        request: AIRequest, 
        provider: AIProviderEnum
    ) -> StandardAIResponse:
        """
        Genera una respuesta usando un proveedor específico.
        """
        if provider not in self.adapters:
            return StandardAIResponse(
                ia_provider_name=provider,
                status=AIResponseStatus.ERROR,
                error_message=f"Proveedor {provider} no disponible",
                latency_ms=0
            )
        
        adapter = self.adapters[provider]
        return await adapter.generate_response(request)
    
    async def generate_parallel_responses(
        self, 
        request: AIRequest, 
        providers: Optional[List[AIProviderEnum]] = None
    ) -> List[StandardAIResponse]:
        """
        Genera respuestas en paralelo de múltiples proveedores.
        """
        if providers is None:
            providers = self.get_available_providers()
        
        # Filtrar solo proveedores disponibles
        available_providers = [p for p in providers if p in self.adapters]
        
        if not available_providers:
            return [StandardAIResponse(
                ia_provider_name=AIProviderEnum.OPENAI,  # Default
                status=AIResponseStatus.ERROR,
                error_message="No hay proveedores disponibles",
                latency_ms=0
            )]
        
        # Ejecutar todas las solicitudes en paralelo
        tasks = [
            self.adapters[provider].generate_response(request)
            for provider in available_providers
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados y excepciones
        processed_responses = []
        for i, response in enumerate(responses):
            provider = available_providers[i]
            
            if isinstance(response, Exception):
                processed_responses.append(StandardAIResponse(
                    ia_provider_name=provider,
                    status=AIResponseStatus.ERROR,
                    error_message=f"Excepción: {str(response)}",
                    latency_ms=0
                ))
            else:
                processed_responses.append(response)
        
        return processed_responses
    
    async def generate_fallback_response(
        self, 
        request: AIRequest, 
        providers: Optional[List[AIProviderEnum]] = None
    ) -> StandardAIResponse:
        """
        Intenta proveedores en orden hasta obtener una respuesta exitosa.
        """
        if providers is None:
            providers = self.get_available_providers()
        
        available_providers = [p for p in providers if p in self.adapters]
        
        if not available_providers:
            return StandardAIResponse(
                ia_provider_name=AIProviderEnum.OPENAI,  # Default
                status=AIResponseStatus.ERROR,
                error_message="No hay proveedores disponibles",
                latency_ms=0
            )
        
        last_response = None
        
        for provider in available_providers:
            response = await self.adapters[provider].generate_response(request)
            
            if response.status == AIResponseStatus.SUCCESS:
                return response
            
            last_response = response
            logger.warning(f"Proveedor {provider} falló, intentando siguiente...")
        
        # Si ninguno funcionó, retornar la última respuesta
        return last_response or StandardAIResponse(
            ia_provider_name=available_providers[-1],
            status=AIResponseStatus.ERROR,
            error_message="Todos los proveedores fallaron",
            latency_ms=0
        )
    
    async def generate_fastest_response(
        self, 
        request: AIRequest, 
        providers: Optional[List[AIProviderEnum]] = None
    ) -> StandardAIResponse:
        """
        Retorna la primera respuesta exitosa (la más rápida).
        """
        if providers is None:
            providers = self.get_available_providers()
        
        available_providers = [p for p in providers if p in self.adapters]
        
        if not available_providers:
            return StandardAIResponse(
                ia_provider_name=AIProviderEnum.OPENAI,  # Default
                status=AIResponseStatus.ERROR,
                error_message="No hay proveedores disponibles",
                latency_ms=0
            )
        
        # Crear tareas para todos los proveedores
        tasks = [
            self.adapters[provider].generate_response(request)
            for provider in available_providers
        ]
        
        # Esperar a que termine la primera exitosa
        for completed_task in asyncio.as_completed(tasks):
            try:
                response = await completed_task
                if response.status == AIResponseStatus.SUCCESS:
                    # Cancelar las tareas restantes
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    return response
            except Exception as e:
                logger.warning(f"Tarea falló: {e}")
                continue
        
        # Si ninguna fue exitosa, esperar a que terminen todas
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Retornar la primera respuesta válida (aunque sea error)
        for response in responses:
            if isinstance(response, StandardAIResponse):
                return response
        
        # Fallback final
        return StandardAIResponse(
            ia_provider_name=available_providers[0],
            status=AIResponseStatus.ERROR,
            error_message="Todas las tareas fallaron",
            latency_ms=0
        )
    
    async def orchestrate(
        self, 
        request: AIRequest, 
        strategy: AIOrchestrationStrategy = AIOrchestrationStrategy.FALLBACK,
        providers: Optional[List[AIProviderEnum]] = None
    ) -> Any:
        """
        Método principal de orquestación que ejecuta la estrategia especificada.
        """
        if strategy == AIOrchestrationStrategy.SINGLE:
            # Si no se especifica proveedor, usar el primero disponible
            if not providers:
                providers = self.get_available_providers()
            
            if not providers:
                return StandardAIResponse(
                    ia_provider_name=AIProviderEnum.OPENAI,
                    status=AIResponseStatus.ERROR,
                    error_message="No hay proveedores disponibles",
                    latency_ms=0
                )
            
            return await self.generate_single_response(request, providers[0])
        
        elif strategy == AIOrchestrationStrategy.PARALLEL:
            return await self.generate_parallel_responses(request, providers)
        
        elif strategy == AIOrchestrationStrategy.FALLBACK:
            return await self.generate_fallback_response(request, providers)
        
        elif strategy == AIOrchestrationStrategy.FASTEST:
            return await self.generate_fastest_response(request, providers)
        
        else:
            raise ValueError(f"Estrategia no soportada: {strategy}")
    
    async def close(self):
        """Cierra todos los adaptadores"""
        for adapter in self.adapters.values():
            await adapter.close() 