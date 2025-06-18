from typing import List, Optional
from uuid import UUID, uuid4
import logging
from datetime import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.database import get_db
from app.crud import project as project_crud
from app.crud import interaction as interaction_crud
from app.schemas.project import Project, ProjectCreate, ProjectUpdate
from app.schemas.interaction import QueryRequest, QueryResponse
from app.schemas.auth import SessionUser
from app.schemas.ai_response import AIRequest
from app.schemas.query import ContextInfo
from app.api.v1.endpoints.auth import get_current_user

# Servicios para orquestación
from app.services.ai_orchestrator import AIOrchestrator
from app.services.ai_moderator import AIModerator
from app.services.context_manager import ContextManager
from app.services.pre_analyst import pre_analyst_service
from app.services.followup_interpreter import create_followup_interpreter

# Sistema de métricas
from app.core.metrics import (
    start_orchestration_metrics,
    complete_orchestration_metrics,
    time_step,
    metrics_collector
)

# Importar modelos adicionales para el dashboard conversacional
from app.models.models import ContextChunk, InteractionEvent, ModeratedSynthesis

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


def require_auth(current_user: Optional[SessionUser] = Depends(get_current_user)) -> SessionUser:
    """Helper para requerir autenticación"""
    # TEMPORALMENTE DESHABILITADO PARA PRUEBAS
    return SessionUser(
        id="550e8400-e29b-41d4-a716-446655440000",  # Usuario mock fijo
        name="Test User",
        email="test@orquix.com",
        image=None
    )
    # if not current_user:
    #     raise HTTPException(
    #         status_code=401,
    #         detail="Autenticación requerida"
    #     )
    # return current_user


# ========================================
# FUNCIONES AUXILIARES PARA ORQUESTACIÓN
# ========================================

async def analyze_followup_continuity(
    user_prompt: str,
    project_id: UUID,
    user_id: UUID,
    db: AsyncSession,
    interaction_id: UUID,
    conversation_mode: str = "auto"
) -> tuple[str, bool]:
    """
    Paso -1: Análisis de continuidad conversacional con FollowUpInterpreter
    
    Args:
        user_prompt: Prompt original del usuario
        project_id: ID del proyecto
        user_id: ID del usuario
        db: Sesión de base de datos
        interaction_id: ID de la interacción para métricas
        
    Returns:
        tuple[enriched_prompt, is_followup]
            - enriched_prompt: Prompt enriquecido con contexto o original si no es continuación
            - is_followup: True si detectó continuidad conversacional
    """
    try:
        with time_step(interaction_id, "followup_analysis") as timer:
            logger.info(f"Analizando continuidad conversacional para proyecto {project_id}")
            
            # Crear instancia del FollowUpInterpreter
            followup_interpreter = create_followup_interpreter(db)
            
            # Ejecutar análisis de continuidad y obtener QueryRequest enriquecido
            query_request = await followup_interpreter.handle_followup(
                user_prompt=user_prompt,
                project_id=project_id,
                user_id=user_id,
                conversation_mode=conversation_mode
            )
            
            # Determinar si es continuación basado en el QueryType
            is_followup = query_request.query_type.value == "follow_up"
            
            # Actualizar métricas
            timer.kwargs["is_followup"] = is_followup
            timer.kwargs["query_type"] = query_request.query_type.value
            timer.kwargs["prompt_enriched"] = len(query_request.user_question) > len(user_prompt)
            
            if is_followup:
                logger.info(f"✅ Continuidad detectada - prompt enriquecido con contexto histórico")
                metrics_collector.add_info(
                    interaction_id,
                    f"Continuidad conversacional detectada - QueryType: {query_request.query_type.value}",
                    "followup_analysis"
                )
            else:
                logger.info(f"ℹ️ Tema nuevo detectado - usando prompt original")
            
            return query_request.user_question, is_followup
            
    except Exception as e:
        logger.warning(f"Error en análisis de continuidad para proyecto {project_id}: {e}")
        metrics_collector.add_error(interaction_id, str(e), "followup_analysis")
        # En caso de error, continuar con el prompt original
        return user_prompt, False


async def pre_analyze_query(
    user_prompt: str,
    project_id: UUID,
    interaction_id: UUID,
    force_analyze: bool = False
) -> tuple[str, bool]:
    """
    Paso 0: Análisis previo de la consulta con PreAnalyst
    
    Args:
        user_prompt: Prompt original del usuario
        project_id: ID del proyecto
        interaction_id: ID de la interacción
        force_analyze: Si True, siempre analiza sin importar la longitud
        
    Returns:
        tuple[refined_prompt, needs_clarification]
            - refined_prompt: Prompt refinado o original si no necesita análisis
            - needs_clarification: True si necesita preguntas de clarificación
    """
    try:
        with time_step(interaction_id, "pre_analysis") as timer:
            logger.info(f"Iniciando pre-análisis para proyecto {project_id}")
            
            # Determinar si necesita pre-análisis
            should_analyze = (
                force_analyze or 
                len(user_prompt.strip()) < 50 or  # Prompts muy cortos
                any(word in user_prompt.lower() for word in [
                    "ayuda", "necesito", "cómo", "qué", "mejor", "recomendación"
                ]) or
                "?" in user_prompt and len(user_prompt) < 100  # Preguntas cortas
            )
            
            if not should_analyze:
                logger.info(f"Pre-análisis omitido: prompt suficientemente específico")
                timer.kwargs["skipped"] = True
                return user_prompt, False
            
            # Ejecutar análisis con PreAnalyst
            analysis_result = await pre_analyst_service.analyze_prompt(user_prompt)
            
            # Actualizar métricas
            timer.kwargs["interpreted_intent"] = analysis_result.interpreted_intent[:100]
            timer.kwargs["clarification_questions_count"] = len(analysis_result.clarification_questions)
            timer.kwargs["has_refined_candidate"] = analysis_result.refined_prompt_candidate is not None
            
            # SIEMPRE usar el refined_prompt_candidate (ahora siempre está presente)
            refined_prompt = analysis_result.refined_prompt_candidate
            has_clarifications = bool(analysis_result.clarification_questions)
            
            if has_clarifications:
                logger.info(f"Pre-análisis sugiere clarificación: {len(analysis_result.clarification_questions)} preguntas")
                logger.info(f"Prompt refinado disponible: {refined_prompt[:100]}...")
                metrics_collector.add_warning(
                    interaction_id,
                    f"Consulta tiene clarificaciones sugeridas: {len(analysis_result.clarification_questions)} preguntas",
                    "pre_analysis"
                )
                # Retornar prompt refinado y señalar que hay clarificaciones disponibles
                return refined_prompt, True
            else:
                logger.info(f"Pre-análisis completado sin clarificaciones: usando prompt refinado")
                return refined_prompt, False
            
    except Exception as e:
        logger.warning(f"Error en pre-análisis para proyecto {project_id}: {e}")
        metrics_collector.add_error(interaction_id, str(e), "pre_analysis")
        # En caso de error, continuar con el prompt original
        return user_prompt, False

async def get_context_for_query(
    context_manager: ContextManager,
    query: str,
    project_id: UUID,
    user_id: UUID,
    interaction_id: UUID,
    include_context: bool = True
) -> tuple[Optional[str], Optional[ContextInfo]]:
    """
    Paso 1: Obtener contexto relevante del proyecto usando el Context Manager
    """
    if not include_context:
        logger.info(f"Contexto deshabilitado para consulta en proyecto {project_id}")
        return None, None
    
    try:
        with time_step(interaction_id, "context_retrieval") as timer:
            logger.info(f"Obteniendo contexto para consulta en proyecto {project_id}")
            
            # Generar bloque de contexto usando el Context Manager
            context_block = await context_manager.generate_context_block(
                query=query,
                project_id=project_id,
                user_id=user_id,
                max_tokens=4000,  # Límite razonable para contexto
                top_k=10,
                similarity_threshold=0.1
            )
            
            # Actualizar métricas
            timer.kwargs["chunks_found"] = context_block.chunks_used
            
            if context_block.chunks_used == 0:
                logger.info(f"No se encontró contexto relevante para proyecto {project_id}")
                metrics_collector.add_warning(
                    interaction_id, 
                    "No se encontró contexto relevante", 
                    "context_retrieval"
                )
                return None, None
            
            # Crear ContextInfo para el frontend
            context_info = ContextInfo(
                total_chunks=context_block.chunks_used,
                avg_similarity=context_block.avg_similarity,
                sources_used=[chunk.source_type for chunk in context_block.chunks],
                total_characters=len(context_block.context_text),
                context_text=context_block.context_text
            )
            
            logger.info(f"Contexto obtenido: {context_block.chunks_used} chunks, {context_block.total_tokens} tokens")
            return context_block.context_text, context_info
        
    except Exception as e:
        logger.warning(f"Error obteniendo contexto para proyecto {project_id}: {e}")
        metrics_collector.add_error(interaction_id, str(e), "context_retrieval")
        # No fallar la consulta por problemas de contexto
        return None, None


async def orchestrate_ai_responses(
    orchestrator: AIOrchestrator,
    user_prompt: str,
    context_text: Optional[str],
    project_id: UUID,
    interaction_id: UUID,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    context_info: Optional[ContextInfo] = None
):
    """
    Paso 2: Orquestar respuestas de múltiples proveedores de IA
    """
    try:
        with time_step(interaction_id, "ai_orchestration") as timer:
            logger.info(f"Iniciando orquestación de IAs para proyecto {project_id}")
            
            # Preparar prompt con contexto si está disponible
            enhanced_prompt = user_prompt
            if context_text:
                enhanced_prompt = f"""Contexto del proyecto:
{context_text}

---

Consulta del usuario:
{user_prompt}

Por favor, responde considerando el contexto proporcionado cuando sea relevante."""

            # Preparar parámetros de orquestación
            ai_request = AIRequest(
                prompt=enhanced_prompt,
                max_tokens=max_tokens or 1000,
                temperature=temperature or 0.7,
                project_id=str(project_id),
                user_id=str(interaction_id)  # Usar interaction_id como user_id temporal
            )
            
            # Ejecutar orquestación usando estrategia PARALLEL
            from app.services.ai_orchestrator import AIOrchestrationStrategy
            ai_responses = await orchestrator.orchestrate(
                ai_request, 
                strategy=AIOrchestrationStrategy.PARALLEL
            )
            
            # Crear objeto de resultado compatible
            class OrchestrationResult:
                def __init__(self, ai_responses, context_info=None):
                    self.ai_responses = ai_responses
                    self.context_info = context_info
            
            orchestration_result = OrchestrationResult(ai_responses, context_info)
            
            if not orchestration_result.ai_responses:
                raise HTTPException(
                    status_code=503,
                    detail="No se pudieron obtener respuestas de los proveedores de IA"
                )
            
            # Actualizar métricas
            responses_count = len(orchestration_result.ai_responses)
            failures_count = sum(1 for resp in orchestration_result.ai_responses if resp.status != "success")
            
            timer.kwargs["responses_count"] = responses_count
            timer.kwargs["failures_count"] = failures_count
            
            if failures_count > 0:
                metrics_collector.add_warning(
                    interaction_id,
                    f"{failures_count} proveedores fallaron",
                    "ai_orchestration"
                )
            
            logger.info(f"Orquestación completada: {responses_count} respuestas, {failures_count} fallos")
            return orchestration_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en orquestación para proyecto {project_id}: {e}")
        metrics_collector.add_error(interaction_id, str(e), "ai_orchestration")
        raise HTTPException(
            status_code=500,
            detail=f"Error en orquestación de IAs: {str(e)}"
        )


async def synthesize_responses(
    moderator: AIModerator,
    ai_responses: list,
    project_id: UUID,
    interaction_id: UUID
):
    """
    Paso 3: Sintetizar respuestas usando el Moderador IA v2.0
    """
    try:
        with time_step(interaction_id, "moderator_synthesis") as timer:
            logger.info(f"Iniciando síntesis con Moderador v2.0 para proyecto {project_id}")
            
            # Verificar que tenemos respuestas para sintetizar
            if not ai_responses:
                raise HTTPException(
                    status_code=400,
                    detail="No hay respuestas para sintetizar"
                )
            
            # Ejecutar síntesis
            synthesis_result = await moderator.synthesize_responses(ai_responses)
            
            if not synthesis_result.synthesis_text:
                raise HTTPException(
                    status_code=500,
                    detail="El moderador no pudo generar una síntesis válida"
                )
            
            # Actualizar métricas
            timer.kwargs["quality"] = synthesis_result.quality.value
            timer.kwargs["fallback_used"] = synthesis_result.fallback_used
            
            if synthesis_result.fallback_used:
                metrics_collector.add_warning(
                    interaction_id,
                    "Se usó el fallback del moderador",
                    "moderator_synthesis"
                )
            
            logger.info(f"Síntesis completada con calidad: {synthesis_result.quality.value}")
            return synthesis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en síntesis para proyecto {project_id}: {e}")
        metrics_collector.add_error(interaction_id, str(e), "moderator_synthesis")
        raise HTTPException(
            status_code=500,
            detail=f"Error en síntesis del moderador: {str(e)}"
        )


async def save_interaction_background(
    project_id: UUID,
    user_id: UUID,
    interaction_id: UUID,
    user_prompt: str,
    ai_responses: list,
    synthesis_result,
    context_text: Optional[str],
    processing_time_ms: int,
    is_followup: bool = False,
    enriched_prompt: Optional[str] = None
):
    """
    Paso 4: Guardar la interacción completa (ejecutado en background)
    """
    try:
        logger.info(f"Guardando interacción {interaction_id} en background")
        
        # Crear una nueva sesión de base de datos para el background task
        from app.core.database import async_session_factory
        
        async with async_session_factory() as db:
            # Preparar datos de la interacción con serialización segura
            def serialize_ai_response(response):
                """Serializar respuesta IA de manera segura"""
                if hasattr(response, 'dict'):
                    data = response.dict()
                else:
                    data = response
                
                # Convertir datetime a string si existe
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, datetime):
                            data[key] = value.isoformat()
                
                return data
            
            interaction_data = {
                "id": str(interaction_id),
                "project_id": str(project_id),
                "user_id": str(user_id),
                "user_prompt": user_prompt,
                "ai_responses": [serialize_ai_response(response) for response in ai_responses],
                "moderator_synthesis": {
                    "synthesis_text": synthesis_result.synthesis_text,
                    "quality": synthesis_result.quality.value,
                    "key_themes": synthesis_result.key_themes,
                    "contradictions": synthesis_result.contradictions,
                    "consensus_areas": synthesis_result.consensus_areas,
                    "recommendations": synthesis_result.recommendations,
                    "suggested_questions": synthesis_result.suggested_questions,
                    "research_areas": synthesis_result.research_areas,
                    "fallback_used": synthesis_result.fallback_used
                },
                "context_used": context_text is not None,
                "context_preview": context_text[:200] + "..." if context_text and len(context_text) > 200 else context_text,
                "processing_time_ms": processing_time_ms,
                "created_at": datetime.utcnow().isoformat(),  # Convertir a string ISO
                # ✅ Metadatos específicos para continuidad conversacional
                "followup_metadata": {
                    "is_followup": is_followup,
                    "enriched_prompt": enriched_prompt,
                    "prompt_enrichment_applied": enriched_prompt is not None and enriched_prompt != user_prompt
                }
            }
            
            # ✅ Logging específico para tracking de continuidad conversacional
            if is_followup:
                logger.info(f"🔗 Continuidad conversacional detectada en interacción {interaction_id}")
                logger.info(f"   - Prompt original: {user_prompt[:100]}...")
                logger.info(f"   - Prompt enriquecido: {enriched_prompt[:100] if enriched_prompt else 'N/A'}...")
            else:
                logger.info(f"🆕 Tema nuevo detectado en interacción {interaction_id}")
            
            # Guardar en base de datos
            await interaction_crud.create_interaction(db, interaction_data)
            await db.commit()
            
        # Opcional: Guardar contexto generado por la respuesta para futuras consultas
        if synthesis_result.synthesis_text:
            async with async_session_factory() as db:
                context_manager = ContextManager(db)
                await context_manager.process_and_store_text(
                    text=synthesis_result.synthesis_text,
                    project_id=project_id,
                    user_id=user_id,
                    source_type="ai_synthesis",
                    source_identifier=str(interaction_id)
                )
                await db.commit()
        
        logger.info(f"✅ Interacción {interaction_id} guardada exitosamente en base de datos")
        
    except Exception as e:
        logger.error(f"❌ Error guardando interacción {interaction_id}: {e}")
        # No fallar la respuesta principal por errores de guardado


# ========================================
# ENDPOINTS CRUD DE PROYECTOS
# ========================================

@router.post("/", response_model=Project)
async def create_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_in: ProjectCreate,
    current_user: SessionUser = Depends(require_auth),
) -> Project:
    """
    POST /api/v1/projects
    
    Crear nuevo proyecto.
    """
    user_id = UUID(current_user.id)
    project = await project_crud.create_project(db=db, obj_in=project_in, user_id=user_id)
    
    logger.info(f"Proyecto creado: {project.id} por usuario {user_id}")
    return project


@router.get("/", response_model=List[Project])
async def read_projects(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: SessionUser = Depends(require_auth),
) -> List[Project]:
    """
    GET /api/v1/projects
    
    Obtener proyectos del usuario autenticado.
    """
    user_id = UUID(current_user.id)
    projects = await project_crud.get_projects_by_user(
        db=db, user_id=user_id, skip=skip, limit=limit
    )
    return projects


@router.get("/{project_id}", response_model=Project)
async def read_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: UUID,
    current_user: SessionUser = Depends(require_auth),
) -> Project:
    """
    GET /api/v1/projects/{project_id}
    
    Obtener proyecto por ID.
    """
    user_id = UUID(current_user.id)
    project = await project_crud.get_project(db=db, id=project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Verificar que el proyecto pertenece al usuario
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este proyecto")
    
    return project


@router.put("/{project_id}", response_model=Project)
async def update_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: UUID,
    project_in: ProjectUpdate,
    current_user: SessionUser = Depends(require_auth),
) -> Project:
    """
    PUT /api/v1/projects/{project_id}
    
    Actualizar parámetros del proyecto (especialmente configuración del moderador).
    """
    user_id = UUID(current_user.id)
    project = await project_crud.get_project(db=db, id=project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Verificar que el proyecto pertenece al usuario
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar este proyecto")
    
    project = await project_crud.update_project(db=db, db_obj=project, obj_in=project_in)
    
    logger.info(f"Proyecto actualizado: {project_id} por usuario {user_id}")
    return project


@router.delete("/{project_id}", response_model=Project)
async def delete_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: UUID,
    current_user: SessionUser = Depends(require_auth),
) -> Project:
    """
    DELETE /api/v1/projects/{project_id}
    
    Eliminar proyecto.
    """
    user_id = UUID(current_user.id)
    project = await project_crud.get_project(db=db, id=project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Verificar que el proyecto pertenece al usuario
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este proyecto")
    
    project = await project_crud.delete_project(db=db, id=project_id)
    
    logger.info(f"Proyecto eliminado: {project_id} por usuario {user_id}")
    return project


# ========================================
# ENDPOINT PRINCIPAL DE ORQUESTACIÓN
# ========================================

@router.post("/{project_id}/query", response_model=QueryResponse)
async def query_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: UUID,
    query_request: QueryRequest,
    background_tasks: BackgroundTasks,
    current_user: SessionUser = Depends(require_auth),
) -> QueryResponse:
    """
    POST /api/v1/projects/{project_id}/query
    
    🎯 ENDPOINT PRINCIPAL DE ORQUESTACIÓN DEL FLUJO CENTRAL
    
    Secuencia completa con PreAnalyst integrado:
    1. Validación de proyecto y permisos
    2. Pre-análisis de la consulta (PreAnalyst)
    3. Obtención de contexto relevante (Context Manager) 
    4. Orquestación de respuestas IA (AI Orchestrator)
    5. Síntesis inteligente (AI Moderator v2.0)
    6. Guardado de interacción (Background Task)
    
    El PreAnalyst mejora automáticamente consultas vagas o ambiguas,
    generando prompts refinados para mejor comprensión contextual.
    
    Manejo robusto de errores en cada paso con rollback automático.
    Métricas completas de observabilidad y rendimiento.
    """
    start_time = datetime.utcnow()
    user_id = UUID(current_user.id)
    interaction_id = uuid4()
    
    # Variables para cleanup
    orchestrator = None
    moderator = None
    context_manager = None
    orchestration_success = False
    
    # Iniciar métricas de orquestación
    metrics = start_orchestration_metrics(interaction_id, project_id, user_id)
    
    try:
        # ========================================
        # PASO 0: VALIDACIÓN Y SETUP
        # ========================================
        
        logger.info(f"🎯 Iniciando consulta {interaction_id} para proyecto {project_id}")
        
        # Verificar que el proyecto existe y pertenece al usuario
        project = await project_crud.get_project(db=db, id=project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        if project.user_id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permisos para consultar este proyecto")
        
        # Inicializar servicios
        orchestrator = AIOrchestrator()
        moderator = AIModerator()
        context_manager = ContextManager(db)
        
        # ========================================
        # PASO 0.5: ANÁLISIS DE CONTINUIDAD CONVERSACIONAL
        # ========================================
        
        enriched_prompt, is_followup = await analyze_followup_continuity(
            user_prompt=query_request.user_prompt_text,
            project_id=project_id,
            user_id=user_id,
            db=db,
            interaction_id=interaction_id,
            conversation_mode=query_request.conversation_mode or "auto"
        )
        
        # ========================================
        # PASO 1: PRE-ANÁLISIS DE LA CONSULTA
        # ========================================
        
        refined_prompt, needs_clarification = await pre_analyze_query(
            user_prompt=enriched_prompt,  # Usar prompt enriquecido si hay continuidad
            project_id=project_id,
            interaction_id=interaction_id,
            force_analyze=False  # Por ahora automático
        )
        
        # Si necesita clarificación, por ahora continuamos con prompt original
        # TODO: Implementar flujo de clarificación iterativo
        effective_prompt = refined_prompt
        
        # ========================================
        # PASO 2: OBTENER CONTEXTO RELEVANTE
        # ========================================
        
        context_text, context_info = await get_context_for_query(
            context_manager=context_manager,
            query=effective_prompt,  # Usar prompt refinado para búsqueda de contexto
            project_id=project_id,
            user_id=user_id,
            interaction_id=interaction_id,
            include_context=query_request.include_context
        )
        
        # ========================================
        # PASO 3: ORQUESTACIÓN DE IAs
        # ========================================
        
        orchestration_result = await orchestrate_ai_responses(
            orchestrator=orchestrator,
            user_prompt=effective_prompt,  # Usar prompt refinado para orquestación
            context_text=context_text,
            project_id=project_id,
            interaction_id=interaction_id,
            temperature=query_request.temperature,
            max_tokens=query_request.max_tokens,
            context_info=context_info
        )
        
        # ========================================
        # PASO 4: SÍNTESIS CON MODERADOR v2.0
        # ========================================
        
        synthesis_result = await synthesize_responses(
            moderator=moderator,
            ai_responses=orchestration_result.ai_responses,
            project_id=project_id,
            interaction_id=interaction_id
        )
        
        # ========================================
        # PASO 5: CALCULAR MÉTRICAS Y RESPUESTA
        # ========================================
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Construir respuesta completa
        response = QueryResponse(
            interaction_event_id=interaction_id,
            synthesis_text=synthesis_result.synthesis_text,
            moderator_quality=synthesis_result.quality.value,
            
            # Meta-análisis v2.0
            key_themes=synthesis_result.key_themes,
            contradictions=synthesis_result.contradictions,
            consensus_areas=synthesis_result.consensus_areas,
            recommendations=synthesis_result.recommendations,
            suggested_questions=synthesis_result.suggested_questions,
            research_areas=synthesis_result.research_areas,
            
            # ✅ AGREGAR ESTA LÍNEA:
            context_info=orchestration_result.context_info,  # Información del contexto utilizado
            
            # Metadatos
            individual_responses=orchestration_result.ai_responses,
            processing_time_ms=processing_time,
            created_at=start_time,
            fallback_used=synthesis_result.fallback_used
        )
        
        # Marcar como exitosa antes del background task
        orchestration_success = True
        
        # ========================================
        # PASO 6: GUARDADO EN BACKGROUND
        # ========================================
        
        # Programar guardado de la interacción como tarea de fondo
        background_tasks.add_task(
            save_interaction_background,
            project_id=project_id,
            user_id=user_id,
            interaction_id=interaction_id,
            user_prompt=query_request.user_prompt_text,  # Guardar prompt original del usuario
            ai_responses=orchestration_result.ai_responses,
            synthesis_result=synthesis_result,
            context_text=context_text,
            processing_time_ms=processing_time,
            # Metadatos adicionales para continuidad conversacional
            is_followup=is_followup,
            enriched_prompt=enriched_prompt if is_followup else None
        )
        
        logger.info(f"✅ Consulta {interaction_id} completada en {processing_time}ms")
        return response
        
    except HTTPException as e:
        # Registrar error específico en métricas
        metrics_collector.add_error(
            interaction_id, 
            f"HTTP {e.status_code}: {e.detail}", 
            "endpoint"
        )
        # Re-lanzar HTTPExceptions para que mantengan su código de estado
        raise
        
    except Exception as e:
        logger.error(f"❌ Error inesperado en consulta {interaction_id}: {e}")
        metrics_collector.add_error(interaction_id, str(e), "endpoint")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )
        
    finally:
        # ========================================
        # CLEANUP DE RECURSOS Y MÉTRICAS
        # ========================================
        
        # Completar métricas de orquestación
        complete_orchestration_metrics(interaction_id, orchestration_success)
        
        cleanup_errors = []
        
        if orchestrator:
            try:
                await orchestrator.close()
            except Exception as e:
                cleanup_errors.append(f"orchestrator: {e}")
        
        if moderator:
            try:
                await moderator.close()
            except Exception as e:
                cleanup_errors.append(f"moderator: {e}")
        
        # El context_manager usa la sesión de base de datos que se cierra automáticamente
        
        if cleanup_errors:
            logger.warning(f"Errores en cleanup para consulta {interaction_id}: {cleanup_errors}")
            # Registrar errores de cleanup en métricas
            for error in cleanup_errors:
                metrics_collector.add_warning(interaction_id, error, "cleanup")

@router.get("/{project_id}/conversation-state")
async def get_conversation_state(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: UUID,
    current_user: SessionUser = Depends(require_auth),
) -> dict:
    """
    GET /api/v1/projects/{project_id}/conversation-state
    
    🔍 DASHBOARD CONVERSACIONAL DETALLADO
    
    Obtiene el estado completo de la conversación para mostrar en la interfaz:
    - Historial de interacciones con metadatos
    - Estado del contexto acumulado
    - Indicadores de continuidad conversacional
    - Métricas de rendimiento
    - Flujo de procesamiento detallado
    """
    user_id = UUID(current_user.id)
    
    try:
        # Verificar permisos
        project = await project_crud.get_project(db=db, id=project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        if project.user_id != user_id:
            raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este proyecto")
        
        # 1. Obtener historial de interacciones con metadatos
        try:
            interactions_stmt = select(InteractionEvent, ModeratedSynthesis).outerjoin(
                ModeratedSynthesis, InteractionEvent.moderated_synthesis_id == ModeratedSynthesis.id
            ).where(
                InteractionEvent.project_id == project_id,
                InteractionEvent.user_id == user_id,
                InteractionEvent.deleted_at.is_(None)
            ).order_by(InteractionEvent.created_at.desc()).limit(10)
            
            interactions_result = await db.exec(interactions_stmt)
            interactions_rows = interactions_result.all()
        except Exception as e:
            logger.warning(f"Error obteniendo interacciones para proyecto {project_id}: {e}")
            interactions_rows = []
        
        # Procesar interacciones
        interactions_history = []
        total_tokens_used = 0
        followup_count = 0
        
        for interaction_event, moderated_synthesis in interactions_rows:
            # Extraer metadatos de continuidad
            followup_metadata = {}
            ai_responses_data = {}
            
            if interaction_event.ai_responses_json:
                try:
                    ai_responses_data = json.loads(interaction_event.ai_responses_json) if isinstance(interaction_event.ai_responses_json, str) else interaction_event.ai_responses_json
                    if isinstance(ai_responses_data, dict) and "followup_metadata" in ai_responses_data:
                        followup_metadata = ai_responses_data["followup_metadata"]
                except:
                    pass
            
            if followup_metadata.get("is_followup", False):
                followup_count += 1
            
            # Calcular tokens aproximados
            prompt_tokens = len(interaction_event.user_prompt_text.split()) * 1.3
            synthesis_tokens = len(moderated_synthesis.synthesis_text.split()) * 1.3 if moderated_synthesis else 0
            total_tokens_used += prompt_tokens + synthesis_tokens
            
            interaction_detail = {
                "id": str(interaction_event.id),
                "user_prompt": interaction_event.user_prompt_text,
                "synthesis_text": moderated_synthesis.synthesis_text if moderated_synthesis else None,
                "created_at": interaction_event.created_at.isoformat(),
                "processing_time_ms": interaction_event.processing_time_ms,
                "context_used": interaction_event.context_used,
                "context_preview": interaction_event.context_preview,
                "followup_metadata": followup_metadata,
                "tokens_estimated": int(prompt_tokens + synthesis_tokens),
                "is_followup": followup_metadata.get("is_followup", False),
                "enriched_prompt": followup_metadata.get("enriched_prompt"),
                "prompt_enrichment_applied": followup_metadata.get("prompt_enrichment_applied", False)
            }
            interactions_history.append(interaction_detail)
        
        # 2. Obtener estado del contexto acumulado
        try:
            context_manager = ContextManager(db)
            
            # Contar chunks de contexto disponibles
            context_chunks_stmt = select(ContextChunk).where(
                ContextChunk.project_id == project_id,
                ContextChunk.user_id == user_id,
                ContextChunk.deleted_at.is_(None)
            )
            context_chunks_result = await db.exec(context_chunks_stmt)
            context_chunks = context_chunks_result.all()
        except Exception as e:
            logger.warning(f"Error obteniendo chunks de contexto para proyecto {project_id}: {e}")
            context_chunks = []
        
        # Agrupar por tipo de fuente
        context_by_source = {}
        total_context_chars = 0
        
        for chunk in context_chunks:
            source_type = chunk.source_type
            if source_type not in context_by_source:
                context_by_source[source_type] = {
                    "count": 0,
                    "total_chars": 0,
                    "sources": set()
                }
            
            context_by_source[source_type]["count"] += 1
            context_by_source[source_type]["total_chars"] += len(chunk.content_text)
            context_by_source[source_type]["sources"].add(chunk.source_identifier)
            total_context_chars += len(chunk.content_text)
        
        # Convertir sets a listas para JSON
        for source_type in context_by_source:
            context_by_source[source_type]["sources"] = list(context_by_source[source_type]["sources"])
        
        # 3. Métricas de rendimiento
        recent_interactions = interactions_history[:5]  # Últimas 5
        avg_processing_time = sum(i.get("processing_time_ms", 0) for i in recent_interactions) / len(recent_interactions) if recent_interactions else 0
        
        # Manejar caso de proyecto nuevo sin interacciones
        if not interactions_history:
            logger.info(f"Proyecto {project_id} no tiene interacciones aún - devolviendo estado inicial")
            return {
                "project_id": str(project_id),
                "project_name": project.name,
                "generated_at": datetime.utcnow().isoformat(),
                "is_new_project": True,
                
                # Historial vacío
                "interactions_history": [],
                
                # Estado del contexto vacío
                "context_state": {
                    "total_chunks": 0,
                    "total_characters": 0,
                    "context_by_source": {},
                    "has_context": False
                },
                
                # Métricas iniciales
                "performance_metrics": {
                    "total_tokens_estimated": 0,
                    "avg_processing_time_ms": 0,
                    "interactions_count": 0,
                    "last_interaction_at": None
                },
                
                # Estado de continuidad inicial
                "continuity_state": {
                    "total_interactions": 0,
                    "followup_interactions": 0,
                    "followup_percentage": 0,
                    "has_active_context": False,
                    "last_interaction_was_followup": False
                },
                
                # Configuración del proyecto
                "project_config": {
                    "moderator_personality": project.moderator_personality,
                    "moderator_temperature": project.moderator_temperature,
                    "moderator_length_penalty": project.moderator_length_penalty
                }
            }
        
        # 4. Estado de continuidad conversacional
        continuity_stats = {
            "total_interactions": len(interactions_history),
            "followup_interactions": followup_count,
            "followup_percentage": round((followup_count / len(interactions_history)) * 100, 1) if interactions_history else 0,
            "has_active_context": len(context_chunks) > 0,
            "last_interaction_was_followup": interactions_history[0]["is_followup"] if interactions_history else False
        }
        
        # 5. Respuesta completa del dashboard
        return {
            "project_id": str(project_id),
            "project_name": project.name,
            "generated_at": datetime.utcnow().isoformat(),
            
            # Historial detallado
            "interactions_history": interactions_history,
            
            # Estado del contexto
            "context_state": {
                "total_chunks": len(context_chunks),
                "total_characters": total_context_chars,
                "context_by_source": context_by_source,
                "has_context": len(context_chunks) > 0
            },
            
            # Métricas de rendimiento
            "performance_metrics": {
                "total_tokens_estimated": int(total_tokens_used),
                "avg_processing_time_ms": round(avg_processing_time, 1),
                "interactions_count": len(interactions_history),
                "last_interaction_at": interactions_history[0]["created_at"] if interactions_history else None
            },
            
            # Estado de continuidad conversacional
            "continuity_state": continuity_stats,
            
            # Estado del proyecto
            "project_config": {
                "moderator_personality": project.moderator_personality,
                "moderator_temperature": project.moderator_temperature,
                "moderator_length_penalty": project.moderator_length_penalty
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado conversacional para proyecto {project_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estado conversacional: {str(e)}"
        ) 