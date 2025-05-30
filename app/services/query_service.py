import time
import asyncio
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlmodel import Session, create_engine

from app.schemas.query import (
    QueryRequest, QueryResponse, ContextInfo, QueryType, ContextConfig
)
from app.schemas.ai_response import (
    AIRequest, StandardAIResponse, AIProviderEnum, AIResponseStatus,
    ErrorCategory, ErrorDetail
)
from app.services.context_manager import ContextManager
from app.services.ai_orchestrator import AIOrchestrator
from app.services.prompt_templates import PromptTemplateManager
from app.core.config import settings

logger = logging.getLogger(__name__)

class QueryService:
    """
    Servicio principal que integra:
    1. Búsqueda de contexto relevante
    2. Construcción de prompts específicos por IA
    3. Ejecución paralela de consultas a múltiples IAs
    4. Agregación de respuestas con manejo robusto de errores
    """
    
    def __init__(self):
        self.context_manager = None
        self.ai_orchestrator = AIOrchestrator()
        self.prompt_manager = PromptTemplateManager()
        
    async def process_query(
        self, 
        query_request: QueryRequest,
        session: Optional[Session] = None
    ) -> QueryResponse:
        """
        Procesa una consulta completa con manejo robusto de errores:
        1. Busca contexto relevante (si aplica)
        2. Construye prompts específicos para cada IA
        3. Ejecuta consultas en paralelo con timeouts
        4. Continúa con respuestas parciales si algunas IAs fallan
        5. Agrega y retorna resultados con métricas detalladas
        """
        start_time = time.time()
        
        try:
            logger.info(f"Procesando consulta: '{query_request.user_question[:50]}...'")
            
            # 1. Buscar contexto relevante si es necesario
            context_info = None
            context_text = ""
            
            if query_request.query_type == QueryType.CONTEXT_AWARE:
                try:
                    context_info, context_text = await self._search_relevant_context(
                        query_request, session
                    )
                except Exception as e:
                    logger.warning(f"Error buscando contexto, continuando sin contexto: {e}")
                    # Continuar sin contexto en lugar de fallar completamente
            
            # 2. Determinar qué IAs usar
            providers_to_use = self._determine_providers(query_request)
            
            if not providers_to_use:
                logger.error("No hay proveedores de IA disponibles")
                return self._create_error_response(
                    query_request, 
                    "No hay proveedores de IA disponibles",
                    int((time.time() - start_time) * 1000)
                )
            
            # 3. Construir prompts específicos y ejecutar en paralelo
            ai_responses = await self._execute_parallel_queries_robust(
                query_request, context_text, providers_to_use
            )
            
            # 4. Verificar si tenemos al menos una respuesta exitosa
            successful_responses = [r for r in ai_responses if r.status == AIResponseStatus.SUCCESS]
            
            # 5. Calcular tiempo de procesamiento
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # 6. Construir respuesta final con métricas detalladas
            response = QueryResponse(
                original_question=query_request.user_question,
                context_info=context_info,
                ai_responses=ai_responses,
                processing_time_ms=processing_time_ms,
                providers_used=providers_to_use,
                metadata=self._build_response_metadata(
                    query_request, ai_responses, providers_to_use, successful_responses
                )
            )
            
            # 7. Log del resultado
            if successful_responses:
                logger.info(f"Consulta completada exitosamente en {processing_time_ms}ms - "
                          f"{len(successful_responses)}/{len(providers_to_use)} proveedores exitosos")
            else:
                logger.warning(f"Consulta completada sin respuestas exitosas en {processing_time_ms}ms")
            
            return response
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Error crítico procesando consulta: {e}")
            
            return self._create_error_response(
                query_request, 
                f"Error crítico del sistema: {str(e)}",
                processing_time_ms
            )
    
    def _create_error_response(
        self, 
        query_request: QueryRequest, 
        error_message: str, 
        processing_time_ms: int
    ) -> QueryResponse:
        """Crea una respuesta de error estándar"""
        return QueryResponse(
            original_question=query_request.user_question,
            ai_responses=[],
            processing_time_ms=processing_time_ms,
            providers_used=[],
            metadata={
                "error": error_message,
                "query_type": query_request.query_type,
                "total_providers": 0,
                "successful_responses": 0,
                "system_failure": True
            }
        )
    
    def _build_response_metadata(
        self,
        query_request: QueryRequest,
        ai_responses: List[StandardAIResponse],
        providers_used: List[AIProviderEnum],
        successful_responses: List[StandardAIResponse]
    ) -> Dict[str, Any]:
        """Construye metadatos detallados de la respuesta"""
        # Análisis de errores
        error_analysis = {}
        for response in ai_responses:
            if response.status != AIResponseStatus.SUCCESS:
                error_type = response.status.value
                if error_type not in error_analysis:
                    error_analysis[error_type] = 0
                error_analysis[error_type] += 1
        
        # Métricas de latencia
        latencies = [r.latency_ms for r in successful_responses]
        latency_stats = {}
        if latencies:
            latency_stats = {
                "min_latency_ms": min(latencies),
                "max_latency_ms": max(latencies),
                "avg_latency_ms": int(sum(latencies) / len(latencies))
            }
        
        # Información de reintentos
        retry_info = {}
        for response in ai_responses:
            if response.retry_info and response.retry_info.total_attempts > 1:
                provider = response.ia_provider_name.value
                retry_info[provider] = {
                    "total_attempts": response.retry_info.total_attempts,
                    "successful_attempt": response.retry_info.successful_attempt,
                    "total_retry_time_ms": response.retry_info.total_retry_time_ms
                }
        
        return {
            "query_type": query_request.query_type,
            "total_providers": len(providers_used),
            "successful_responses": len(successful_responses),
            "failed_responses": len(ai_responses) - len(successful_responses),
            "success_rate": len(successful_responses) / len(ai_responses) if ai_responses else 0,
            "error_analysis": error_analysis,
            "latency_stats": latency_stats,
            "retry_info": retry_info,
            "has_context": query_request.query_type == QueryType.CONTEXT_AWARE,
            "providers_attempted": [p.value for p in providers_used]
        }
    
    async def _search_relevant_context(
        self, 
        query_request: QueryRequest, 
        session: Optional[Session]
    ) -> tuple[Optional[ContextInfo], str]:
        """Busca contexto relevante para la consulta"""
        try:
            if not session:
                # Crear sesión temporal para búsqueda
                database_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
                engine = create_engine(database_url, echo=False)
                session = Session(engine)
            
            # Inicializar context manager si no existe
            if not self.context_manager:
                self.context_manager = ContextManager(session)
            
            # Buscar chunks relevantes
            query_embedding = await self.context_manager.generate_embedding(query_request.user_question)
            
            # Importar la función de búsqueda
            from app.crud.context import find_similar_chunks_sync
            
            config = query_request.context_config or ContextConfig()
            
            # Convertir umbral de similitud
            cosine_threshold = None
            if config.similarity_threshold:
                cosine_threshold = 1 - config.similarity_threshold
            
            chunks = find_similar_chunks_sync(
                db=session,
                query_embedding=query_embedding,
                project_id=query_request.project_id,
                user_id=query_request.user_id,
                top_k=config.top_k,
                similarity_threshold=cosine_threshold
            )
            
            if not chunks:
                logger.info("No se encontró contexto relevante")
                return None, ""
            
            # Formatear contexto
            context_data = []
            total_chars = 0
            
            for chunk in chunks:
                if total_chars >= config.max_context_length:
                    break
                    
                chunk_text = chunk.content_text
                if total_chars + len(chunk_text) > config.max_context_length:
                    # Truncar el último chunk si es necesario
                    remaining = config.max_context_length - total_chars
                    chunk_text = chunk_text[:remaining-3] + "..."
                
                # Calcular similitud (approximada desde distancia coseno)
                import numpy as np
                vec1 = np.array(query_embedding)
                vec2 = np.array(chunk.content_embedding)
                similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                similarity = max(0.0, min(1.0, similarity))
                
                context_data.append({
                    'content_text': chunk_text,
                    'source_type': chunk.source_type,
                    'similarity_score': similarity
                })
                
                total_chars += len(chunk_text)
            
            # Crear texto de contexto formateado
            context_text = self._format_context_for_multiple_providers(context_data)
            
            # Crear información del contexto
            context_info = ContextInfo(
                total_chunks=len(context_data),
                avg_similarity=sum(c['similarity_score'] for c in context_data) / len(context_data),
                sources_used=list(set(c['source_type'] for c in context_data)),
                total_characters=total_chars,
                context_text=context_text
            )
            
            logger.info(f"Contexto encontrado: {len(chunks)} chunks, {total_chars} caracteres")
            return context_info, context_text
            
        except Exception as e:
            logger.error(f"Error buscando contexto: {e}")
            return None, ""
    
    def _determine_providers(self, query_request: QueryRequest) -> List[AIProviderEnum]:
        """Determina qué proveedores de IA usar"""
        if query_request.ai_providers:
            # Usar los proveedores especificados
            available = self.ai_orchestrator.get_available_providers()
            return [p for p in query_request.ai_providers if p in available]
        else:
            # Usar todos los proveedores disponibles
            return self.ai_orchestrator.get_available_providers()
    
    async def _execute_parallel_queries_robust(
        self,
        query_request: QueryRequest,
        context_text: str,
        providers: List[AIProviderEnum]
    ) -> List[StandardAIResponse]:
        """
        Ejecuta consultas a múltiples IAs en paralelo con manejo robusto:
        - Timeouts individuales por proveedor
        - Continuación con respuestas parciales
        - Manejo de excepciones sin interrumpir otras consultas
        - Logging detallado de errores
        """
        if not providers:
            logger.warning("No hay proveedores disponibles")
            return []
        
        # Crear tareas con timeout individual para cada proveedor
        tasks = []
        
        for provider in providers:
            # Timeout específico por proveedor (puede ser configurado)
            provider_timeout = getattr(settings, f'{provider.value.upper()}_TIMEOUT', 30)
            
            task = asyncio.create_task(
                self._query_single_provider_with_timeout(
                    provider, query_request, context_text, provider_timeout
                )
            )
            tasks.append((provider, task))
        
        # Ejecutar todas las tareas en paralelo con gather que no falla por una excepción
        logger.info(f"Ejecutando consultas paralelas a {len(providers)} proveedores")
        
        responses = []
        completed_tasks = 0
        
        # Usar asyncio.as_completed para manejar respuestas conforme van llegando
        for provider, task in tasks:
            try:
                response = await task
                responses.append(response)
                completed_tasks += 1
                
                logger.info(f"✅ {provider.value}: {response.status.value} "
                          f"({response.latency_ms}ms) [{completed_tasks}/{len(providers)}]")
                
            except asyncio.TimeoutError:
                # Timeout específico del proveedor
                timeout_response = StandardAIResponse(
                    ia_provider_name=provider,
                    status=AIResponseStatus.TIMEOUT,
                    error_message=f"Timeout después de {provider_timeout}s",
                    error_detail=ErrorDetail(
                        category=ErrorCategory.NETWORK,
                        code="PROVIDER_TIMEOUT",
                        message=f"Proveedor {provider.value} excedió timeout de {provider_timeout}s"
                    ),
                    latency_ms=provider_timeout * 1000
                )
                responses.append(timeout_response)
                completed_tasks += 1
                
                logger.warning(f"⏰ {provider.value}: TIMEOUT después de {provider_timeout}s "
                             f"[{completed_tasks}/{len(providers)}]")
                
            except Exception as e:
                # Excepción inesperada
                error_response = StandardAIResponse(
                    ia_provider_name=provider,
                    status=AIResponseStatus.ERROR,
                    error_message=f"Excepción inesperada: {str(e)}",
                    error_detail=ErrorDetail(
                        category=ErrorCategory.INTERNAL,
                        code="UNEXPECTED_ERROR",
                        message=str(e)
                    ),
                    latency_ms=0
                )
                responses.append(error_response)
                completed_tasks += 1
                
                logger.error(f"❌ {provider.value}: ERROR - {str(e)} "
                           f"[{completed_tasks}/{len(providers)}]")
        
        # Estadísticas finales
        successful = len([r for r in responses if r.status == AIResponseStatus.SUCCESS])
        logger.info(f"Consultas paralelas completadas: {successful}/{len(providers)} exitosas")
        
        return responses
    
    async def _query_single_provider_with_timeout(
        self,
        provider: AIProviderEnum,
        query_request: QueryRequest,
        context_text: str,
        timeout_seconds: int
    ) -> StandardAIResponse:
        """Consulta a un proveedor específico con timeout"""
        try:
            # Aplicar timeout a toda la operación
            return await asyncio.wait_for(
                self._query_single_provider(provider, query_request, context_text),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            raise  # Re-lanzar para manejo en el nivel superior
        except Exception as e:
            # Cualquier otra excepción se maneja aquí
            logger.error(f"Error interno consultando {provider}: {e}")
            return StandardAIResponse(
                ia_provider_name=provider,
                status=AIResponseStatus.ERROR,
                error_message=f"Error interno: {str(e)}",
                error_detail=ErrorDetail(
                    category=ErrorCategory.INTERNAL,
                    code="INTERNAL_ERROR",
                    message=str(e)
                ),
                latency_ms=0
            )
    
    async def _query_single_provider(
        self,
        provider: AIProviderEnum,
        query_request: QueryRequest,
        context_text: str
    ) -> StandardAIResponse:
        """Consulta a un proveedor específico"""
        try:
            # 1. Construir prompt específico para este proveedor
            prompt_data = self.prompt_manager.build_prompt_for_provider(
                provider=provider,
                user_question=query_request.user_question,
                context_text=context_text,
                additional_vars={
                    'timestamp': str(query_request.conversation_id or ''),
                    'project_name': str(query_request.project_id)[:8] + '...'
                }
            )
            
            # 2. Optimizar prompt para el proveedor
            optimized_prompt = self.prompt_manager.optimize_prompt_for_provider(
                provider, prompt_data, query_request.max_tokens
            )
            
            # 3. Crear request para el AI orchestrator
            ai_request = AIRequest(
                prompt=optimized_prompt['user_message'],
                system_message=optimized_prompt['system_message'],
                max_tokens=query_request.max_tokens,
                temperature=query_request.temperature,
                user_id=str(query_request.user_id) if query_request.user_id else None,
                project_id=str(query_request.project_id),
                conversation_id=query_request.conversation_id
            )
            
            # 4. Ejecutar consulta
            response = await self.ai_orchestrator.generate_single_response(
                ai_request, provider
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error consultando {provider}: {e}")
            return StandardAIResponse(
                ia_provider_name=provider,
                status=AIResponseStatus.ERROR,
                error_message=f"Error interno: {str(e)}",
                latency_ms=0
            )
    
    def _format_context_for_multiple_providers(self, context_data: List[Dict]) -> str:
        """Formatea el contexto de manera neutral para todos los proveedores"""
        if not context_data:
            return ""
        
        context_parts = []
        
        for i, chunk in enumerate(context_data, 1):
            chunk_text = f"""--- Fragmento {i} ---
Fuente: {chunk['source_type']}
Relevancia: {chunk['similarity_score']:.1%}

{chunk['content_text']}

"""
            context_parts.append(chunk_text)
        
        return "\n".join(context_parts)
    
    def get_best_response(self, responses: List[StandardAIResponse]) -> Optional[StandardAIResponse]:
        """
        Selecciona la mejor respuesta basándose en criterios simples.
        En versiones futuras esto podría ser más sofisticado.
        """
        successful_responses = [r for r in responses if r.status == AIResponseStatus.SUCCESS]
        
        if not successful_responses:
            return None
        
        # Por ahora, seleccionar la respuesta más rápida y exitosa
        return min(successful_responses, key=lambda r: r.latency_ms)
    
    async def close(self):
        """Cierra recursos"""
        if self.ai_orchestrator:
            await self.ai_orchestrator.close() 