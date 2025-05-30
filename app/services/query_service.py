import time
import asyncio
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlmodel import Session, create_engine

from app.schemas.query import (
    QueryRequest, QueryResponse, ContextInfo, QueryType, ContextConfig
)
from app.schemas.ai_response import AIRequest, StandardAIResponse, AIProviderEnum, AIResponseStatus
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
    4. Agregación de respuestas
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
        Procesa una consulta completa:
        1. Busca contexto relevante (si aplica)
        2. Construye prompts específicos para cada IA
        3. Ejecuta consultas en paralelo
        4. Agrega y retorna resultados
        """
        start_time = time.time()
        
        try:
            logger.info(f"Procesando consulta: '{query_request.user_question[:50]}...'")
            
            # 1. Buscar contexto relevante si es necesario
            context_info = None
            context_text = ""
            
            if query_request.query_type == QueryType.CONTEXT_AWARE:
                context_info, context_text = await self._search_relevant_context(
                    query_request, session
                )
            
            # 2. Determinar qué IAs usar
            providers_to_use = self._determine_providers(query_request)
            
            # 3. Construir prompts específicos y ejecutar en paralelo
            ai_responses = await self._execute_parallel_queries(
                query_request, context_text, providers_to_use
            )
            
            # 4. Calcular tiempo de procesamiento
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # 5. Construir respuesta final
            response = QueryResponse(
                original_question=query_request.user_question,
                context_info=context_info,
                ai_responses=ai_responses,
                processing_time_ms=processing_time_ms,
                providers_used=providers_to_use,
                metadata={
                    "query_type": query_request.query_type,
                    "total_providers": len(providers_to_use),
                    "successful_responses": len([r for r in ai_responses if r.status == AIResponseStatus.SUCCESS])
                }
            )
            
            logger.info(f"Consulta completada en {processing_time_ms}ms")
            return response
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Error procesando consulta: {e}")
            
            # Respuesta de error
            return QueryResponse(
                original_question=query_request.user_question,
                ai_responses=[],
                processing_time_ms=processing_time_ms,
                providers_used=[],
                metadata={"error": str(e)}
            )
    
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
    
    async def _execute_parallel_queries(
        self,
        query_request: QueryRequest,
        context_text: str,
        providers: List[AIProviderEnum]
    ) -> List[StandardAIResponse]:
        """Ejecuta consultas a múltiples IAs en paralelo"""
        if not providers:
            logger.warning("No hay proveedores disponibles")
            return []
        
        # Crear tareas para cada proveedor
        tasks = []
        
        for provider in providers:
            task = self._query_single_provider(
                provider, query_request, context_text
            )
            tasks.append(task)
        
        # Ejecutar todas las tareas en paralelo
        logger.info(f"Ejecutando consultas paralelas a {len(providers)} proveedores")
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados y excepciones
        processed_responses = []
        
        for i, response in enumerate(responses):
            provider = providers[i]
            
            if isinstance(response, Exception):
                # Crear respuesta de error para excepciones
                error_response = StandardAIResponse(
                    ia_provider_name=provider,
                    status=AIResponseStatus.ERROR,
                    error_message=f"Excepción durante consulta: {str(response)}",
                    latency_ms=0
                )
                processed_responses.append(error_response)
                logger.error(f"Error en {provider}: {response}")
            else:
                processed_responses.append(response)
                logger.info(f"Respuesta de {provider}: {response.status}")
        
        return processed_responses
    
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