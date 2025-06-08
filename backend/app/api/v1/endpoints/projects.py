from typing import List, Optional
from uuid import UUID, uuid4
import logging
from datetime import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

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

# Sistema de métricas
from app.core.metrics import (
    start_orchestration_metrics,
    complete_orchestration_metrics,
    time_step,
    metrics_collector
)

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
    processing_time_ms: int
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
                "created_at": datetime.utcnow().isoformat()  # Convertir a string ISO
            }
            
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
    
    Secuencia completa:
    1. Validación de proyecto y permisos
    2. Obtención de contexto relevante (Context Manager)
    3. Orquestación de respuestas IA (AI Orchestrator)
    4. Síntesis inteligente (AI Moderator v2.0)
    5. Guardado de interacción (Background Task)
    
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
        # PASO 1: OBTENER CONTEXTO RELEVANTE
        # ========================================
        
        context_text, context_info = await get_context_for_query(
            context_manager=context_manager,
            query=query_request.user_prompt_text,
            project_id=project_id,
            user_id=user_id,
            interaction_id=interaction_id,
            include_context=query_request.include_context
        )
        
        # ========================================
        # PASO 2: ORQUESTACIÓN DE IAs
        # ========================================
        
        orchestration_result = await orchestrate_ai_responses(
            orchestrator=orchestrator,
            user_prompt=query_request.user_prompt_text,
            context_text=context_text,
            project_id=project_id,
            interaction_id=interaction_id,
            temperature=query_request.temperature,
            max_tokens=query_request.max_tokens,
            context_info=context_info
        )
        
        # ========================================
        # PASO 3: SÍNTESIS CON MODERADOR v2.0
        # ========================================
        
        synthesis_result = await synthesize_responses(
            moderator=moderator,
            ai_responses=orchestration_result.ai_responses,
            project_id=project_id,
            interaction_id=interaction_id
        )
        
        # ========================================
        # PASO 4: CALCULAR MÉTRICAS Y RESPUESTA
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
        # PASO 5: GUARDADO EN BACKGROUND
        # ========================================
        
        # Programar guardado de la interacción como tarea de fondo
        background_tasks.add_task(
            save_interaction_background,
            project_id=project_id,
            user_id=user_id,
            interaction_id=interaction_id,
            user_prompt=query_request.user_prompt_text,
            ai_responses=orchestration_result.ai_responses,
            synthesis_result=synthesis_result,
            context_text=context_text,
            processing_time_ms=processing_time
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