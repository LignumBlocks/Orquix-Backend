import logging
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.auth import SessionUser
from app.crud import session as session_crud
from app.crud import chat as chat_crud
from app.crud import ia_prompt as ia_prompt_crud
from app.crud import interaction as interaction_crud
# Schemas temporales para compatibilidad (migrar gradualmente a Chat + Session)
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import json

# Funciones de compatibilidad para migrar gradualmente del sistema antiguo al nuevo
async def _get_or_create_default_chat(db: AsyncSession, project_id: UUID, user_id: UUID) -> UUID:
    """Obtiene o crea un chat por defecto para el proyecto."""
    # Obtener chats del proyecto
    chats = await chat_crud.get_chats_by_project(db, project_id)
    
    # Filtrar por usuario (la función get_chats_by_project no filtra por user_id)
    user_chats = [chat for chat in chats if chat.user_id == user_id]
    
    if user_chats:
        return user_chats[0].id
    else:
        # Crear chat por defecto
        chat = await chat_crud.create_chat(
            db=db,
            project_id=project_id,
            user_id=user_id,
            title="Construcción de Contexto"
        )
        return chat.id

async def _get_context_session_compat(db: AsyncSession, session_id: UUID):
    """Función de compatibilidad para obtener sesión."""
    # En el sistema nuevo, buscamos en la tabla sessions
    session = await session_crud.get_session(db, session_id)
    if session:
        # Convertir a formato compatible con el sistema antiguo
        return type('MockInteractionEvent', (), {
            'id': session.id,
            'project_id': session.chat.project_id if hasattr(session, 'chat') else None,
            'user_id': session.user_id,
            'context_used_summary': session.accumulated_context,
            'ai_responses_json': '[]',  # Historial vacío por ahora
            'session_status': session.status,
            'created_at': session.started_at,
            'updated_at': session.updated_at
        })()
    return None

async def _create_context_session_compat(db: AsyncSession, project_id: UUID, user_id: UUID, initial_message: str = None):
    """Función de compatibilidad para crear sesión."""
    # Obtener o crear chat por defecto
    chat_id = await _get_or_create_default_chat(db, project_id, user_id)
    
    # Crear sesión en el sistema nuevo
    session = await session_crud.create_session(
        db=db,
        chat_id=chat_id,
        user_id=user_id,
        accumulated_context="",
        status="active"
    )
    
    # Convertir a formato compatible
    return type('MockInteractionEvent', (), {
        'id': session.id,
        'project_id': project_id,
        'user_id': session.user_id,
        'context_used_summary': session.accumulated_context,
        'ai_responses_json': '[]',
        'session_status': session.status,
        'created_at': session.started_at,
        'updated_at': session.updated_at
    })()

def _convert_session_to_context_session(session_data):
    """Convierte una sesión al formato ContextSession."""
    return ContextSession(
        id=session_data.id,
        project_id=session_data.project_id,
        user_id=session_data.user_id,
        conversation_history=[],  # Por ahora vacío
        accumulated_context=session_data.context_used_summary or "",
        is_active=(session_data.session_status == "active"),
        created_at=session_data.created_at,
        updated_at=session_data.updated_at
    )

class ContextMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime
    message_type: Optional[str] = None

class ContextChatRequest(BaseModel):
    user_message: str
    session_id: Optional[UUID] = None

class ContextChatResponse(BaseModel):
    session_id: UUID
    ai_response: str
    message_type: str
    accumulated_context: str
    suggestions: List[str] = []
    context_elements_count: int = 0

class ContextFinalizeRequest(BaseModel):
    session_id: UUID
    final_question: str

class ContextSessionSummary(BaseModel):
    id: UUID
    project_id: UUID
    accumulated_context: str
    messages_count: int
    is_active: bool
    created_at: datetime
    last_activity: datetime

class ContextSession(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    conversation_history: List[ContextMessage]
    accumulated_context: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Funciones de compatibilidad adicionales (después de las definiciones de clases)
async def _update_context_session_compat(db: AsyncSession, session_data, new_message: ContextMessage, updated_context: str):
    """Función de compatibilidad para actualizar sesión de contexto."""
    # Actualizar contexto acumulado en la sesión
    await session_crud.update_session_context(db, session_data.id, updated_context)
    
    # ✅ NUEVO: Crear evento de timeline para el mensaje del usuario
    if new_message.role == "user":
        await interaction_crud.create_timeline_event(
            db=db,
            session_id=session_data.id,
            event_type="user_message",
            content=new_message.content,
            event_data={
                "message_type": new_message.message_type,
                "timestamp": new_message.timestamp.isoformat()
            },
            project_id=session_data.project_id,  # Compatibilidad
            user_id=session_data.user_id  # Compatibilidad
        )
    
    # Hacer commit para guardar el evento
    await db.commit()
    
    return session_data

async def _get_project_context_sessions_compat(db: AsyncSession, project_id: UUID, user_id: UUID) -> List[ContextSessionSummary]:
    """Función de compatibilidad para obtener sesiones de proyecto."""
    # Obtener chats del proyecto
    chats = await chat_crud.get_chats_by_project(db, project_id)
    
    # Filtrar por usuario
    user_chats = [chat for chat in chats if chat.user_id == user_id]
    summaries = []
    
    for chat in user_chats:
        # Obtener sesiones del chat
        sessions = await session_crud.get_sessions_by_chat(db, chat.id)
        for session in sessions:
            summaries.append(ContextSessionSummary(
                id=session.id,
                project_id=project_id,
                accumulated_context=session.accumulated_context,
                messages_count=0,  # Por ahora 0
                is_active=(session.status == "active"),
                created_at=session.started_at,
                last_activity=session.updated_at
            ))
    
    return summaries

async def _finalize_context_session_compat(db: AsyncSession, session_id: UUID):
    """Función de compatibilidad para finalizar sesión."""
    return await session_crud.update_session_status(db, session_id, "completed")

async def _get_active_session_for_project_compat(db: AsyncSession, project_id: UUID, user_id: UUID):
    """Función de compatibilidad para obtener sesión activa."""
    try:
        # Obtener chats del proyecto
        chats = await chat_crud.get_chats_by_project(db, project_id)
        
        # Buscar en todos los chats del proyecto
        for chat in chats:
            # Buscar sesión activa en el chat
            active_session = await session_crud.get_active_session(db, chat.id)
            if active_session and active_session.user_id == user_id:
                # Convertir a formato compatible
                return type('MockInteractionEvent', (), {
                    'id': active_session.id,
                    'project_id': project_id,
                    'user_id': active_session.user_id,
                    'context_used_summary': active_session.accumulated_context,
                    'ai_responses_json': '[]',
                    'session_status': active_session.status,
                    'created_at': active_session.started_at,
                    'updated_at': active_session.updated_at
                })()
        
        # Si no hay sesión activa, crear una en el primer chat disponible
        if chats:
            first_chat = chats[0]
            logger.info(f"🆕 No hay sesión activa, creando nueva en chat {first_chat.id}")
            
            # Usar la nueva función para obtener o crear sesión activa
            active_session = await session_crud.get_or_create_active_session(
                db=db,
                chat_id=first_chat.id,
                user_id=user_id
            )
            
            # Convertir a formato compatible
            return type('MockInteractionEvent', (), {
                'id': active_session.id,
                'project_id': project_id,
                'user_id': active_session.user_id,
                'context_used_summary': active_session.accumulated_context,
                'ai_responses_json': '[]',
                'session_status': active_session.status,
                'created_at': active_session.started_at,
                'updated_at': active_session.updated_at
            })()
        
        return None
        
    except Exception as e:
        logger.error(f"Error buscando/creando sesión activa para proyecto {project_id}: {e}")
        return None

from app.schemas.ia_prompt import (
    GeneratePromptRequest,
    GeneratePromptResponse,
    ExecutePromptRequest,
    IAPromptResponse,
    IAPromptUpdate
)
from app.services.context_builder import context_builder_service
from app.services.prompt_templates import PromptTemplateManager
from app.schemas.ai_response import AIProviderEnum

logger = logging.getLogger(__name__)

router = APIRouter()

async def _automatically_include_moderator_synthesis(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    current_context: str
) -> str:
    """
    Busca automáticamente síntesis del moderador reciente y la incluye en el contexto.
    
    Args:
        db: Sesión de base de datos
        project_id: ID del proyecto
        user_id: ID del usuario
        current_context: Contexto actual acumulado
        
    Returns:
        Contexto mejorado con síntesis del moderador (si está disponible)
    """
    try:
        from sqlalchemy import select, and_, desc
        from app.models.models import InteractionEvent
        import json
        
        # Buscar la interacción más reciente con síntesis del moderador
        stmt = select(InteractionEvent).where(
            and_(
                InteractionEvent.project_id == project_id,
                InteractionEvent.user_id == user_id,
                InteractionEvent.event_type == "moderator_synthesis",
                InteractionEvent.deleted_at.is_(None)
            )
        ).order_by(desc(InteractionEvent.created_at)).limit(1)
        
        result = await db.execute(stmt)
        recent_interaction = result.scalar_one_or_none()
        
        if not recent_interaction:
            # No hay síntesis del moderador disponible
            logger.debug(f"No se encontró síntesis del moderador para proyecto {project_id}")
            return current_context
        
        # Verificar si la síntesis ya está incluida en el contexto
        if "🔬 Análisis del Moderador IA" in current_context:
            logger.debug("Síntesis del moderador ya incluida en el contexto")
            return current_context
        
        # Parsear la síntesis del moderador desde event_data
        moderator_data = recent_interaction.event_data if recent_interaction.event_data else {}
        
        logger.info(f"✨ Incluyendo automáticamente síntesis del moderador - Calidad: {moderator_data.get('quality', 'unknown')}")
        
        # Incluir la síntesis en el contexto usando el método del context builder
        enhanced_context = context_builder_service.include_moderator_synthesis(
            current_context=current_context,
            synthesis_text=moderator_data.get('synthesis_text', ''),
            key_themes=moderator_data.get('key_themes', []),
            recommendations=moderator_data.get('recommendations', [])
        )
        
        logger.info(f"🧠 Contexto enriquecido automáticamente - Anterior: {len(current_context)} chars, Nuevo: {len(enhanced_context)} chars")
        
        return enhanced_context
        
    except Exception as e:
        logger.warning(f"Error incluyendo síntesis del moderador automáticamente: {e}")
        # En caso de error, devolver el contexto original
        return current_context

def require_auth(current_user: Optional[SessionUser] = Depends(get_current_user)) -> SessionUser:
    """Require authentication for protected endpoints."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return current_user


@router.post(
    "/projects/{project_id}/context-chat",
    response_model=ContextChatResponse,
    summary="Chat para construcción de contexto",
    description="Endpoint para chatear y construir contexto antes de enviar a las IAs principales"
)
async def context_chat(
    project_id: UUID,
    request: ContextChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """
    Procesa un mensaje del usuario en la construcción de contexto.
    
    - Si no hay session_id, crea una nueva sesión
    - Si hay session_id, continúa la conversación existente
    - Usa GPT-3.5 para generar respuestas conversacionales
    """
    try:
        user_id = UUID(current_user.id)  # Convertir string a UUID
        logger.info(f"💬 Context chat - Proyecto: {project_id}, Usuario: {user_id}")
        logger.info(f"💬 Tipos - project_id: {type(project_id)}, user_id: {type(user_id)}")
        
        # Obtener o crear sesión
        if request.session_id:
            # Continuar sesión existente
            # Convertir explícitamente a UUID si viene como string
            session_uuid = request.session_id
            if isinstance(session_uuid, str):
                session_uuid = UUID(session_uuid)
            
            logger.info(f"🔍 Buscando sesión existente: {session_uuid} (tipo: {type(session_uuid)})")
            db_session = await _get_context_session_compat(db, session_uuid)
            logger.info(f"📋 Sesión encontrada: {db_session is not None}")
            
            # Validar que la sesión pertenece al proyecto y usuario correctos
            if db_session:
                logger.info(f"📋 Sesión details: project_id={db_session.project_id}, user_id={db_session.user_id}, status={db_session.session_status}")
                logger.info(f"📋 Comparación project_id: {db_session.project_id} == {project_id} -> {db_session.project_id == project_id}")
                logger.info(f"📋 Comparación user_id: {db_session.user_id} == {user_id} -> {db_session.user_id == user_id}")
                
                # Si la sesión no pertenece al proyecto/usuario actual, crear una nueva
                if db_session.project_id != project_id or db_session.user_id != user_id:
                    logger.warning(f"⚠️ Sesión {session_uuid} pertenece a otro proyecto/usuario. Creando nueva sesión.")
                    db_session = await _create_context_session_compat(
                        db, project_id, user_id, request.user_message
                    )
            else:
                # Sesión no encontrada, crear nueva
                logger.info(f"🆕 Sesión {session_uuid} no encontrada. Creando nueva sesión.")
                db_session = await _create_context_session_compat(
                    db, project_id, user_id, request.user_message
                )
        else:
            # Crear nueva sesión
            logger.info(f"🆕 Creando nueva sesión para proyecto {project_id}")
            db_session = await _create_context_session_compat(
                db, project_id, user_id, request.user_message
            )
        
        # Convertir a modelo Pydantic para trabajar con el servicio
        session = _convert_session_to_context_session(db_session)
        
        # Buscar síntesis del moderador reciente y agregar automáticamente al contexto
        enhanced_context = await _automatically_include_moderator_synthesis(
            db=db,
            project_id=project_id,
            user_id=user_id,
            current_context=session.accumulated_context
        )
        
        # Obtener historial real de interaction_events de la sesión
        from app.crud import interaction as interaction_crud
        conversation_history = []
        try:
            timeline_events = await interaction_crud.get_session_timeline(
                db=db,
                session_id=db_session.id,
                limit=50  # Últimos 50 eventos para el chat
            )
            
            logger.info(f"📜 Historial cargado: {len(timeline_events)} eventos para sesión {db_session.id}")
            
            # Convertir eventos a mensajes de conversación
            for event in timeline_events:
                if event.event_type == "user_message":
                    conversation_history.append(ContextMessage(
                        role="user",
                        content=event.content,
                        timestamp=event.created_at,
                        message_type="user"
                    ))
                    logger.info(f"📝 Usuario: {event.content[:50]}...")
                elif event.event_type == "ai_response":
                    conversation_history.append(ContextMessage(
                        role="assistant", 
                        content=event.content,
                        timestamp=event.created_at,
                        message_type="assistant"
                    ))
                    logger.info(f"🤖 IA: {event.content[:50]}...")
            
            logger.info(f"💬 Historial final: {len(conversation_history)} mensajes para el Context Builder")
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de conversación: {e}")
            conversation_history = []  # Usar historial vacío en caso de error
        
        # Procesar mensaje con GPT-3.5 usando el historial real de la sesión
        response = await context_builder_service.process_user_message(
            user_message=request.user_message,
            conversation_history=conversation_history,
            current_context=enhanced_context
        )
        
        # Actualizar session_id con el real
        response.session_id = db_session.id
        
        # Crear mensajes para actualizar la sesión
        user_message = ContextMessage(
            role="user",
            content=request.user_message,
            timestamp=datetime.utcnow(),
            message_type="information" if response.message_type == "information" else "question"
        )
        
        ai_message = ContextMessage(
            role="assistant",
            content=response.ai_response,
            timestamp=datetime.utcnow(),
            message_type=response.message_type
        )
        
        # Actualizar sesión con mensaje del usuario
        await _update_context_session_compat(
            db=db,
            session_data=db_session,
            new_message=user_message,
            updated_context=response.accumulated_context
        )
        
        # Crear evento para la respuesta de la IA
        await interaction_crud.create_timeline_event(
            db=db,
            session_id=db_session.id,
            event_type="ai_response",
            content=response.ai_response,
            event_data={
                "message_type": response.message_type,
                "suggestions": response.suggestions,
                "context_elements_count": response.context_elements_count,
                "timestamp": datetime.utcnow().isoformat()
            },
            project_id=db_session.project_id,
            user_id=db_session.user_id
        )
        
        # Actualizar contexto acumulado en la sesión
        await session_crud.update_session_context(db, db_session.id, response.accumulated_context)
        
        # Hacer commit final
        await db.commit()
        
        logger.info(f"✅ Context chat procesado - Sesión: {response.session_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error en context chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando mensaje: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/context-sessions",
    response_model=List[ContextSessionSummary],
    summary="Listar sesiones de contexto",
    description="Obtiene las sesiones de construcción de contexto de un proyecto"
)
async def get_context_sessions(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """
    Obtiene las sesiones de contexto de un proyecto.
    """
    try:
        user_id = UUID(current_user.id)  # Convertir string a UUID
        sessions = await _get_project_context_sessions_compat(
            db=db,
            project_id=project_id,
            user_id=user_id
        )
        return sessions
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo sesiones de contexto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo sesiones: {str(e)}"
        )


@router.get(
    "/context-sessions/{session_id}",
    response_model=ContextSession,
    summary="Obtener sesión de contexto",
    description="Obtiene una sesión de contexto específica con todo su historial"
)
async def get_context_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """
    Obtiene una sesión de contexto específica.
    """
    try:
        user_id = UUID(current_user.id)  # Convertir string a UUID
        db_session = await _get_context_session_compat(db, session_id)
        if not db_session or db_session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión de contexto no encontrada"
            )
        
        # Convertir a modelo Pydantic para acceder a los campos correctamente
        session_model = _convert_session_to_context_session(db_session)
        return session_model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo sesión de contexto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo sesión: {str(e)}"
        )


@router.post(
    "/context-sessions/{session_id}/finalize",
    summary="Finalizar construcción de contexto",
    description="Finaliza la construcción de contexto y envía la consulta a las IAs principales"
)
async def finalize_context_session(
    session_id: UUID,
    request: ContextFinalizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """
    Finaliza la construcción de contexto y envía la consulta a las IAs principales.
    
    Este endpoint:
    1. Marca la sesión como finalizada
    2. Toma el contexto acumulado + pregunta final
    3. Lo envía al flujo normal de IAs principales
    """
    try:
        user_id = UUID(current_user.id)  # Convertir string a UUID
        logger.info(f"🏁 Finalizando sesión de contexto: {session_id}")
        
        # Obtener y validar sesión
        db_session = await _get_context_session_compat(db, session_id)
        if not db_session or db_session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión de contexto no encontrada"
            )
        
        if db_session.session_status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La sesión ya está finalizada"
            )
        
        # Finalizar sesión
        await _finalize_context_session_compat(db, session_id)
        
        # TODO: Aquí se integraría con el flujo normal de IAs principales
        # Por ahora retornamos información de la finalización
        
        return {
            "message": "Sesión de contexto finalizada exitosamente",
            "session_id": session_id,
            "accumulated_context": db_session.context_used_summary,
            "final_question": request.final_question,
            "ready_for_ai_processing": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error finalizando sesión de contexto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finalizando sesión: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/active-context-session",
    response_model=ContextSession,
    summary="Obtener sesión activa",
    description="Obtiene la sesión de contexto activa para un proyecto"
)
async def get_active_context_session(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """
    Obtiene la sesión de contexto activa para un proyecto.
    """
    try:
        user_id = UUID(current_user.id)  # Convertir string a UUID
        db_session = await _get_active_session_for_project_compat(
            db=db,
            project_id=project_id,
            user_id=user_id
        )
        
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay sesión de contexto activa"
            )
        
        session = _convert_session_to_context_session(db_session)
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo sesión activa: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo sesión activa: {str(e)}"
        )


@router.post("/context-sessions/{session_id}/generate-ai-prompts")
async def generate_ai_prompts(
    session_id: UUID,
    request: ContextFinalizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Genera los prompts reales usando el query_service y prompt_templates.
    Muestra exactamente los prompts que se enviarían a cada IA.
    """
    logger.info(f"🎯 Generando prompts usando query_service - Sesión: {session_id}")
    
    try:
        # Verificar que la sesión existe y pertenece al usuario
        session = await _get_context_session_compat(db, session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Sesión de contexto no encontrada"
            )
        
        user_id = UUID(current_user.id)  # Convertir string a UUID
        if session.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para acceder a esta sesión"
            )
        
        # Convertir a modelo Pydantic para acceder a los campos correctamente
        session_model = _convert_session_to_context_session(session)
        
        # Importar los servicios correctos
        from app.services.query_service import QueryService
        from app.services.prompt_templates import PromptTemplateManager
        from app.schemas.ai_response import AIProviderEnum
        from app.schemas.query import QueryRequest, QueryType
        from app.core.config import settings
        
        # Crear instancias de los servicios
        query_service = QueryService()
        prompt_manager = PromptTemplateManager()
        
        # Determinar proveedores disponibles
        available_providers = []
        if settings.OPENAI_API_KEY:
            available_providers.append(AIProviderEnum.OPENAI)
        if settings.ANTHROPIC_API_KEY:
            available_providers.append(AIProviderEnum.ANTHROPIC)
        
        if not available_providers:
            raise HTTPException(
                status_code=500,
                detail="No hay proveedores de IA configurados"
            )
        
        # Crear una QueryRequest simulada para obtener los prompts
        query_request = QueryRequest(
            user_question=request.final_question,
            query_type=QueryType.CONTEXT_AWARE,
            user_id=user_id,
            project_id=session.project_id,
            max_tokens=1200,
            temperature=0.7
        )
        
        # Usar el contexto acumulado de la sesión
        context_text = session_model.accumulated_context or ""
        
        # Generar prompts para cada proveedor usando el sistema oficial
        ai_prompts = {}
        
        for provider in available_providers:
            try:
                # Usar el método oficial del query_service para construir prompts
                prompt_data = prompt_manager.build_prompt_for_provider(
                    provider=provider,
                    user_question=query_request.user_question,
                    context_text=context_text,
                    additional_vars={
                        'timestamp': datetime.utcnow().isoformat(),
                        'project_name': f"Proyecto-{str(session.project_id)[:8]}"
                    }
                )
                
                # Optimizar el prompt para el proveedor
                optimized_prompt = prompt_manager.optimize_prompt_for_provider(
                    provider, prompt_data, query_request.max_tokens
                )
                
                # Obtener modelo específico del proveedor
                if provider == AIProviderEnum.OPENAI:
                    model = "gpt-4o-mini"
                elif provider == AIProviderEnum.ANTHROPIC:
                    model = "claude-3-haiku-20240307"
                else:
                    model = "unknown"
                
                ai_prompts[provider.value.lower()] = {
                    "provider": f"{provider.value.title()}",
                    "model": model,
                    "system_message": optimized_prompt['system_message'],
                    "user_prompt": optimized_prompt['user_message'],
                    "parameters": {
                        "max_tokens": query_request.max_tokens,
                        "temperature": query_request.temperature
                    },
                    "template_used": "prompt_templates_v2.0"
                }
                
            except Exception as e:
                logger.error(f"Error generando prompt para {provider}: {e}")
                ai_prompts[provider.value.lower()] = {
                    "provider": f"{provider.value.title()}",
                    "error": f"Error generando prompt: {str(e)}"
                }
        
        logger.info(f"✅ Prompts generados usando query_service para {len(ai_prompts)} proveedores")
        
        return {
            "session_id": session_id,
            "ai_prompts": ai_prompts,
            "prompt_system": "query_service + prompt_templates",
            "context_used": context_text[:200] + "..." if len(context_text) > 200 else context_text,
            "final_question": request.final_question
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando prompts con query_service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando prompts: {str(e)}"
        )


@router.post("/context-sessions/{session_id}/query-ais")
async def query_ais_individually(
    session_id: UUID,
    request: ContextFinalizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Endpoint específico para enviar los prompts a las IAs y obtener respuestas individuales.
    Se ejecuta después de generar los prompts.
    """
    logger.info(f"🤖 Consultando IAs individualmente - Sesión: {session_id}")
    
    try:
        # Verificar que la sesión existe y pertenece al usuario
        session = await _get_context_session_compat(db, session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Sesión de contexto no encontrada"
            )
        
        user_id = UUID(current_user.id)
        if session.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para acceder a esta sesión"
            )
        
        # Convertir a modelo Pydantic
        session_model = _convert_session_to_context_session(session)
        
        # Importar servicios necesarios
        from app.services.ai_orchestrator import AIOrchestrator
        from app.schemas.ai_response import AIRequest, AIProviderEnum
        from app.core.config import settings
        import time
        
        # PASO 1: Generar prompts automáticamente usando PromptTemplateManager
        from app.services.prompt_templates import PromptTemplateManager
        prompt_manager = PromptTemplateManager()
        
        logger.info(f"🎯 Generando prompts automáticamente usando prompt_manager - Sesión: {session_id}")
        
        # Generar prompts para cada proveedor
        prompts_by_provider = {}
        context_text = session_model.accumulated_context or ""
        
        for provider in [AIProviderEnum.OPENAI, AIProviderEnum.ANTHROPIC]:
            try:
                prompt_dict = prompt_manager.build_prompt_for_provider(
                    provider=provider,
                    user_question=request.final_question,
                    context_text=context_text
                )
                # Combinar system y user message en un solo prompt
                full_prompt = f"{prompt_dict['system_message']}\n\n{prompt_dict['user_message']}"
                
                prompts_by_provider[provider.value.lower()] = {
                    'prompt': full_prompt,
                    'system_message': prompt_dict['system_message'],
                    'user_message': prompt_dict['user_message']
                }
            except Exception as e:
                logger.warning(f"Error generando prompt para {provider.value}: {e}")
                # Fallback básico
                fallback_prompt = f"Responde la siguiente pregunta en español basándote en el contexto proporcionado:\n\nContexto: {context_text}\n\nPregunta: {request.final_question}"
                prompts_by_provider[provider.value.lower()] = {
                    'prompt': fallback_prompt,
                    'system_message': "Eres un asistente útil que responde en español.",
                    'user_message': fallback_prompt
                }
        
        # Crear estructura compatible con el código existente
        prompts_result = {
            'prompts_by_provider': prompts_by_provider,
            'context_summary': context_text[:500] + "..." if len(context_text) > 500 else context_text
        }
        
        logger.info(f"✅ Prompts generados para {len(prompts_by_provider)} proveedores")
        
        # PASO 2: Crear instancia del orquestador para enviar prompts
        orchestrator = AIOrchestrator()
        
        # Usar los prompts generados en lugar de crear uno genérico
        prompts_by_provider = prompts_result.get('prompts_by_provider', {})
        
        # Ejecutar consultas individuales a las IAs
        start_time = time.time()
        individual_responses = []
        
        # Obtener proveedores disponibles
        available_providers = orchestrator.get_available_providers()
        
        # Consultar cada proveedor individualmente usando sus prompts específicos
        for provider in available_providers:
            provider_name = provider.value.lower()
            logger.info(f"🤖 Consultando {provider.value.title()}...")
            provider_start = time.time()
            
            # Obtener el prompt específico para este proveedor
            provider_prompt_data = prompts_by_provider.get(provider_name, {})
            if not provider_prompt_data:
                logger.warning(f"⚠️ No se encontró prompt para {provider.value.title()}, saltando...")
                continue
            
            prompt_text = provider_prompt_data.get('prompt', '')
            if not prompt_text:
                logger.warning(f"⚠️ Prompt vacío para {provider.value.title()}, saltando...")
                continue
            
            try:
                # Crear AIRequest específico para este proveedor
                ai_request = AIRequest(
                    prompt=prompt_text,
                    max_tokens=1200,
                    temperature=0.7,
                    user_id=str(user_id),
                    project_id=str(session.project_id)
                )
                
                ai_response = await orchestrator.generate_single_response(
                    request=ai_request,
                    provider=provider
                )
                provider_time = time.time() - provider_start
                
                # Determinar modelo según el proveedor
                model = "gpt-4o-mini" if provider == AIProviderEnum.OPENAI else "claude-3-haiku-20240307"
                
                if ai_response.status.value == "success":
                    # PASO 3: Guardar prompt y respuesta en BD (sin bloquear si falla)
                    try:
                        await save_ia_response_with_prompt(
                            db=db,
                            project_id=session.project_id,
                            provider=provider_name,
                            prompt_text=prompt_text,
                            response_text=ai_response.response_text,
                            latency_ms=int(provider_time * 1000),
                            user_question=request.final_question
                        )
                    except Exception as save_error:
                        logger.warning(f"⚠️ Error guardando respuesta de {provider_name}: {save_error}")
                    
                    individual_responses.append({
                        "provider": provider_name,
                        "model": model,
                        "content": ai_response.response_text,
                        "processing_time_ms": int(provider_time * 1000),
                        "success": True,
                        "timestamp": datetime.utcnow().isoformat(),
                        "prompt_used": prompt_text[:200] + "..." if len(prompt_text) > 200 else prompt_text
                    })
                    logger.info(f"✅ {provider.value.title()} respondió en {provider_time:.2f}s")
                else:
                    # Guardar error también (sin bloquear si falla)
                    try:
                        await save_ia_response_with_prompt(
                            db=db,
                            project_id=session.project_id,
                            provider=provider_name,
                            prompt_text=prompt_text,
                            response_text="",
                            latency_ms=int(provider_time * 1000),
                            user_question=request.final_question,
                            error_message=ai_response.error_message
                        )
                    except Exception as save_error:
                        logger.warning(f"⚠️ Error guardando error de {provider_name}: {save_error}")
                    
                    individual_responses.append({
                        "provider": provider_name,
                        "model": model,
                        "error": ai_response.error_message or "Error desconocido",
                        "processing_time_ms": int(provider_time * 1000),
                        "success": False,
                        "timestamp": datetime.utcnow().isoformat(),
                        "prompt_used": prompt_text[:200] + "..." if len(prompt_text) > 200 else prompt_text
                    })
                    logger.error(f"❌ Error en {provider.value.title()}: {ai_response.error_message}")
                
            except Exception as e:
                provider_time = time.time() - provider_start
                logger.error(f"❌ Error en {provider.value.title()}: {e}")
                
                # Guardar error en BD (sin bloquear si falla)
                try:
                    await save_ia_response_with_prompt(
                        db=db,
                        project_id=session.project_id,
                        provider=provider_name,
                        prompt_text=prompt_text,
                        response_text="",
                        latency_ms=int(provider_time * 1000),
                        user_question=request.final_question,
                        error_message=str(e)
                    )
                except Exception as save_error:
                    logger.warning(f"⚠️ Error guardando excepción de {provider_name}: {save_error}")
                
                individual_responses.append({
                    "provider": provider_name,
                    "model": "gpt-4o-mini" if provider == AIProviderEnum.OPENAI else "claude-3-haiku-20240307",
                    "error": str(e),
                    "processing_time_ms": int(provider_time * 1000),
                    "success": False,
                    "timestamp": datetime.utcnow().isoformat(),
                    "prompt_used": prompt_text[:200] + "..." if len(prompt_text) > 200 else prompt_text
                })
        
        total_time = time.time() - start_time
        successful_responses = [r for r in individual_responses if r.get("success", False)]
        
        # Guardar las respuestas en la base de datos para uso posterior del moderador
        try:
            import json
            ai_responses_data = {
                "responses": individual_responses,
                "user_question": request.final_question,
                "timestamp": datetime.utcnow().isoformat(),
                "total_processing_time_ms": int(total_time * 1000)
            }
            
            # Actualizar la sesión con las respuestas de IAs
            session.ai_responses_json = json.dumps(ai_responses_data)
            await db.commit()
            logger.info(f"💾 Respuestas guardadas en BD para sesión: {session_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error guardando respuestas en BD: {e}")
            # No fallar el endpoint por esto, solo registrar el warning
        
        logger.info(f"✅ Consulta individual completada - {len(successful_responses)}/{len(individual_responses)} exitosas en {total_time:.2f}s")
        
        return {
            "session_id": session_id,
            "user_question": request.final_question,
            "individual_responses": individual_responses,
            "total_processing_time_ms": int(total_time * 1000),
            "successful_responses": len(successful_responses),
            "total_responses": len(individual_responses),
            "prompts_generated": prompts_result,
            "prompts_saved_to_db": True,
            "context_used": prompts_result.get('context_summary', '')[:200] + "..." if len(prompts_result.get('context_summary', '')) > 200 else prompts_result.get('context_summary', ''),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error consultando IAs individualmente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando IAs: {str(e)}"
        )


@router.post("/context-sessions/{session_id}/retry-ai/{provider}")
async def retry_single_ai(
    session_id: UUID,
    provider: str,
    request: ContextFinalizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reintenta consultar una IA específica que falló anteriormente.
    """
    logger.info(f"🔄 Reintentando {provider.upper()} - Sesión: {session_id}")
    
    try:
        # Verificar que la sesión existe y pertenece al usuario
        session = await _get_context_session_compat(db, session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Sesión de contexto no encontrada"
            )

        user_id = current_user.get("user_id")
        if session.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes acceso a esta sesión"
            )

        # Obtener el modelo de sesión para el contexto
        session_model = _convert_session_to_context_session(session)
        if not session_model:
            raise HTTPException(
                status_code=404,
                detail="Modelo de sesión no encontrado"
            )

        # Importar servicios necesarios
        from app.services.ai_orchestrator import AIOrchestrator
        from app.schemas.ai_response import AIRequest
        import time

        # Crear instancia del orquestrador
        orchestrator = AIOrchestrator()
        
        # Usar el contexto acumulado de la sesión
        context_text = session_model.accumulated_context or ""
        
        # Crear prompt completo
        full_prompt = f"""Contexto:
{context_text}

Pregunta del usuario:
{request.final_question}

Por favor, proporciona una respuesta detallada basada en el contexto proporcionado."""

        ai_request = AIRequest(
            prompt=full_prompt,
            max_tokens=1200,
            temperature=0.7,
            user_id=str(user_id),
            project_id=str(session.project_id)
        )

        # Mapear el proveedor string a enum
        from app.services.ai_adapters.base import AIProviderEnum
        provider_map = {
            "openai": AIProviderEnum.OPENAI,
            "anthropic": AIProviderEnum.ANTHROPIC
        }
        
        if provider.lower() not in provider_map:
            raise HTTPException(
                status_code=400,
                detail=f"Proveedor no válido: {provider}. Debe ser 'openai' o 'anthropic'"
            )

        provider_enum = provider_map[provider.lower()]
        
        # Ejecutar consulta individual
        start_time = time.time()
        logger.info(f"🤖 Reintentando {provider.upper()}...")
        
        ai_response = await orchestrator.generate_single_response(ai_request, provider_enum)
        provider_time = time.time() - start_time
        
        # Procesar respuesta
        if ai_response.status.value == "success":
            response_data = {
                "provider": provider.lower(),
                "model": ai_response.model,
                "content": ai_response.response_text,
                "processing_time_ms": int(provider_time * 1000),
                "success": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.info(f"✅ {provider.upper()} respondió correctamente en {provider_time:.2f}s")
        else:
            response_data = {
                "provider": provider.lower(),
                "model": ai_response.model or "unknown",
                "error": ai_response.error_message or "Error desconocido",
                "processing_time_ms": int(provider_time * 1000),
                "success": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.error(f"❌ {provider.upper()} falló nuevamente: {ai_response.error_message}")

        total_time = time.time() - start_time
        
        return {
            "session_id": str(session_id),
            "provider": provider.lower(),
            "response": response_data,
            "total_processing_time_ms": int(total_time * 1000),
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error reintentando {provider}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno reintentando {provider}: {str(e)}"
        )


@router.post("/context-sessions/{session_id}/generate-moderator-prompt")
async def generate_moderator_prompt(
    session_id: UUID,
    request: ContextFinalizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Genera y muestra el prompt que se enviará al moderador para la síntesis,
    sin ejecutar la síntesis real.
    """
    try:
        logger.info(f"📝 Generando prompt del moderador - Sesión: {session_id}")
        
        # Verificar sesión
        db_session = await _get_context_session_compat(db, session_id)
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada"
            )
        
        # Verificar que hay respuestas de IAs disponibles
        if not hasattr(db_session, 'ai_responses_json') or not db_session.ai_responses_json:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay respuestas de IAs disponibles para generar el prompt del moderador"
            )
        
        # Parsear las respuestas de IAs desde JSON
        import json
        ai_responses_data = json.loads(db_session.ai_responses_json)
        
        # Manejar diferentes formatos de datos (puede ser lista o diccionario)
        if isinstance(ai_responses_data, list):
            responses_list = ai_responses_data
        elif isinstance(ai_responses_data, dict):
            responses_list = ai_responses_data.get('responses', [])
        else:
            responses_list = []
        
        # Verificar que hay respuestas exitosas
        successful_responses = [
            resp for resp in responses_list
            if resp.get('success', False) and resp.get('content')
        ]
        
        if not successful_responses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay respuestas exitosas de IAs para generar el prompt del moderador"
            )
        
        # Crear objetos StandardAIResponse simulados para generar el prompt
        from app.schemas.ai_response import StandardAIResponse, AIResponseStatus, AIProviderEnum
        
        # DEBUG: Agregar logging para ver los datos
        logger.info(f"🔍 DEBUG - ai_responses_data type: {type(ai_responses_data)}")
        logger.info(f"🔍 DEBUG - responses_list length: {len(responses_list)}")
        logger.info(f"🔍 DEBUG - successful_responses length: {len(successful_responses)}")
        
        mock_responses = []
        for i, resp_data in enumerate(successful_responses):
            logger.info(f"🔍 DEBUG - Response {i}: {resp_data}")
            
            provider_name = resp_data.get('provider', 'unknown').lower()
            provider_enum = AIProviderEnum.OPENAI if provider_name == 'openai' else AIProviderEnum.ANTHROPIC
            
            # DEBUG: Verificar campos específicos
            content = resp_data.get('content', '')
            processing_time = resp_data.get('processing_time_ms', 0)
            logger.info(f"🔍 DEBUG - content type: {type(content)}, processing_time type: {type(processing_time)}, value: {processing_time}")
            
            mock_response = StandardAIResponse(
                response_text=content,
                status=AIResponseStatus.SUCCESS,
                ia_provider_name=provider_enum,
                latency_ms=processing_time,
                error_message=None,
                timestamp=datetime.utcnow()
            )
            mock_responses.append(mock_response)
        
        # Crear instancia del moderador solo para generar el prompt
        from app.services.ai_moderator import AIModerator
        moderator = AIModerator()
        
        # Generar el prompt usando el método interno
        moderator_prompt = moderator._create_synthesis_prompt(mock_responses)
        
        if not moderator_prompt:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo generar el prompt del moderador"
            )
        
        # Preparar metadatos
        response_data = {
            "session_id": str(session_id),
            "moderator_prompt": moderator_prompt,
            "prompt_length": len(moderator_prompt),
            "responses_count": len(successful_responses),
            "providers_included": [resp.get('provider', 'unknown') for resp in successful_responses],
            "generated_at": datetime.utcnow().isoformat(),
            "prompt_preview": moderator_prompt[:200] + "..." if len(moderator_prompt) > 200 else moderator_prompt
        }
        
        logger.info(f"✅ Prompt del moderador generado - Longitud: {len(moderator_prompt)} caracteres")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generando prompt del moderador: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando prompt del moderador: {str(e)}"
        )


@router.post("/context-sessions/{session_id}/synthesize")
async def synthesize_ai_responses(
    session_id: UUID,
    request: ContextFinalizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Ejecuta la síntesis del moderador usando las respuestas de las IAs guardadas.
    """
    try:
        logger.info(f"🔬 Ejecutando síntesis del moderador - Sesión: {session_id}")
        
        # Verificar sesión
        db_session = await _get_context_session_compat(db, session_id)
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada"
            )
        
        # Buscar respuestas de IAs en la tabla ia_responses usando el context_session_id
        from sqlalchemy import select
        from app.models.models import IAResponse, IAPrompt
        
        # Buscar prompts asociados a esta sesión
        prompts_query = select(IAPrompt).where(
            IAPrompt.context_session_id == session_id,
            IAPrompt.deleted_at.is_(None)
        )
        prompts_result = await db.execute(prompts_query)
        prompts = prompts_result.scalars().all()
        
        if not prompts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay prompts asociados a esta sesión"
            )
        
        logger.info(f"📋 Encontrados {len(prompts)} prompts para la sesión {session_id}")
        
        # Buscar respuestas de IAs para estos prompts
        prompt_ids = [prompt.id for prompt in prompts]
        responses_query = select(IAResponse).where(
            IAResponse.ia_prompt_id.in_(prompt_ids),
            IAResponse.deleted_at.is_(None),
            IAResponse.error_message.is_(None)  # Solo respuestas exitosas
        )
        responses_result = await db.execute(responses_query)
        ia_responses = responses_result.scalars().all()
        
        if not ia_responses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay respuestas exitosas de IAs para sintetizar"
            )
        
        logger.info(f"✅ Encontradas {len(ia_responses)} respuestas exitosas de IAs")
        
        # Crear objetos StandardAIResponse para la síntesis
        from app.schemas.ai_response import StandardAIResponse, AIResponseStatus, AIProviderEnum
        
        mock_responses = []
        for ia_response in ia_responses:
            # Determinar el proveedor
            provider_name = ia_response.ia_provider_name.lower()
            if provider_name == 'openai':
                provider_enum = AIProviderEnum.OPENAI
            elif provider_name == 'anthropic':
                provider_enum = AIProviderEnum.ANTHROPIC
            else:
                provider_enum = AIProviderEnum.OPENAI  # Default
            
            mock_response = StandardAIResponse(
                response_text=ia_response.raw_response_text,
                status=AIResponseStatus.SUCCESS,
                ia_provider_name=provider_enum,
                latency_ms=ia_response.latency_ms,
                error_message=None,
                timestamp=ia_response.received_at
            )
            mock_responses.append(mock_response)
        
        logger.info(f"🔄 Preparadas {len(mock_responses)} respuestas para síntesis")
        
        # Ejecutar síntesis del moderador
        from app.services.ai_moderator import AIModerator
        moderator = AIModerator()
        
        import time
        start_time = time.time()
        synthesis_result = await moderator.synthesize_responses(mock_responses)
        synthesis_time = time.time() - start_time
        
        if not synthesis_result or not synthesis_result.synthesis_text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo generar la síntesis del moderador"
            )
        
        # Preparar respuesta estructurada
        response_data = {
            "session_id": str(session_id),
            "synthesis": {
                "text": synthesis_result.synthesis_text,
                "quality": synthesis_result.quality.value if synthesis_result.quality else "unknown",
                "key_themes": synthesis_result.key_themes,
                "consensus_areas": synthesis_result.consensus_areas,
                "contradictions": synthesis_result.contradictions,
                "recommendations": synthesis_result.recommendations,
                "suggested_questions": synthesis_result.suggested_questions,
                "research_areas": synthesis_result.research_areas,
                "connections": synthesis_result.connections,
                "source_references": synthesis_result.source_references
            },
            "metadata": {
                "responses_analyzed": len(ia_responses),
                "providers_included": [resp.ia_provider_name for resp in ia_responses],
                "synthesis_time_ms": int(synthesis_time * 1000),
                "processing_time_ms": synthesis_result.processing_time_ms,
                "original_responses_count": synthesis_result.original_responses_count,
                "successful_responses_count": synthesis_result.successful_responses_count,
                "fallback_used": synthesis_result.fallback_used,
                "meta_analysis_quality": synthesis_result.meta_analysis_quality,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"✅ Síntesis completada - {len(ia_responses)} respuestas analizadas en {synthesis_time:.2f}s")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error ejecutando síntesis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ejecutando síntesis: {str(e)}"
        )


# ================================
# NUEVOS ENDPOINTS PARA FLUJO DE PROMPTS
# ================================

@router.post("/projects/{project_id}/generate-prompt")
async def generate_prompt_for_project(
    project_id: UUID,
    request: GeneratePromptRequest,
    current_user: SessionUser = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
) -> GeneratePromptResponse:
    """
    Genera un prompt para las IAs basado en la consulta del usuario.
    Este es el primer paso del flujo: generar -> editar (opcional) -> ejecutar
    """
    try:
        logger.info(f"🎯 Generando prompt para proyecto {project_id} - Query: {request.query[:100]}...")
        
        # Obtener contexto si hay session_id
        context_data = ""
        if request.context_session_id:
            db_session = await _get_context_session_compat(db, request.context_session_id)
            if db_session:
                session_model = _convert_session_to_context_session(db_session)
                context_data = session_model.accumulated_context
                logger.info(f"📋 Usando contexto de sesión {request.context_session_id} - {len(context_data)} chars")
        
        # Generar prompt usando el template universal
        from app.services.prompt_templates import PromptTemplateManager
        from app.schemas.ai_response import AIProviderEnum
        
        prompt_manager = PromptTemplateManager()
        prompt_data = prompt_manager.build_prompt_for_provider(
            provider=AIProviderEnum.OPENAI,  # Usamos OpenAI como referencia (ambos usan el mismo template)
            user_question=request.query,
            context_text=context_data
        )
        
        # Combinar system y user message en un solo prompt
        generated_prompt = f"{prompt_data['system_message']}\n\n{prompt_data['user_message']}"
        
        # Guardar el prompt en la base de datos
        ia_prompt = await ia_prompt_crud.create_ia_prompt(
            db=db,
            project_id=project_id,
            context_session_id=request.context_session_id,
            original_query=request.query,
            generated_prompt=generated_prompt
        )
        
        logger.info(f"✅ Prompt generado y guardado - ID: {ia_prompt.id}, Longitud: {len(generated_prompt)} chars")
        
        # ✅ NUEVO: Crear evento de timeline para la generación del prompt
        if request.context_session_id:
            try:
                await interaction_crud.create_timeline_event(
                    db=db,
                    session_id=request.context_session_id,
                    event_type="prompt_generated",
                    content=f"Prompt generado para consulta: {request.query}",
                    event_data={
                        "prompt_id": str(ia_prompt.id),
                        "query": request.query,
                        "prompt_length": len(generated_prompt),
                        "context_used": len(context_data) > 0,
                        "context_length": len(context_data),
                        "generated_at": datetime.utcnow().isoformat()
                    },
                    project_id=project_id,  # Compatibilidad
                    user_id=UUID(current_user.id)  # Compatibilidad
                )
                await db.commit()
                logger.info(f"📝 Evento de timeline creado para generación de prompt - Sesión: {request.context_session_id}")
            except Exception as timeline_error:
                logger.warning(f"⚠️ Error creando evento de timeline: {timeline_error}")
                # No fallar la operación principal por esto
                pass
        
        return GeneratePromptResponse(
            prompt_id=ia_prompt.id,
            original_query=ia_prompt.original_query,
            generated_prompt=ia_prompt.generated_prompt,
            project_id=ia_prompt.project_id,
            context_session_id=ia_prompt.context_session_id,
            status=ia_prompt.status,
            created_at=ia_prompt.created_at
        )
        
    except Exception as e:
        logger.error(f"❌ Error generando prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando prompt: {str(e)}"
        )


@router.get("/prompts/{prompt_id}")
async def get_prompt_by_id(
    prompt_id: UUID,
    current_user: SessionUser = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
) -> IAPromptResponse:
    """
    Obtiene un prompt específico por su ID, incluyendo sus respuestas de IA si las tiene.
    """
    try:
        ia_prompt = await ia_prompt_crud.get_ia_prompt_by_id(db, prompt_id)
        if not ia_prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt no encontrado"
            )
        
        return IAPromptResponse.from_orm(ia_prompt)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo prompt {prompt_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo prompt: {str(e)}"
        )


@router.put("/prompts/{prompt_id}")
async def update_prompt(
    prompt_id: UUID,
    request: IAPromptUpdate,
    current_user: SessionUser = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
) -> IAPromptResponse:
    """
    Actualiza un prompt con una versión editada por el usuario.
    """
    try:
        logger.info(f"✏️ Actualizando prompt {prompt_id} con versión editada")
        
        updated_prompt = await ia_prompt_crud.update_ia_prompt(
            db=db,
            prompt_id=prompt_id,
            edited_prompt=request.edited_prompt
        )
        
        if not updated_prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt no encontrado"
            )
        
        logger.info(f"✅ Prompt {prompt_id} actualizado - Nuevo status: {updated_prompt.status}")
        
        # ✅ NUEVO: Crear evento de timeline para la edición del prompt
        if updated_prompt.context_session_id:
            try:
                await interaction_crud.create_timeline_event(
                    db=db,
                    session_id=updated_prompt.context_session_id,
                    event_type="prompt_edited",
                    content=f"Prompt editado por el usuario",
                    event_data={
                        "prompt_id": str(updated_prompt.id),
                        "original_length": len(updated_prompt.generated_prompt),
                        "edited_length": len(request.edited_prompt),
                        "length_change": len(request.edited_prompt) - len(updated_prompt.generated_prompt),
                        "edited_at": datetime.utcnow().isoformat()
                    },
                    project_id=updated_prompt.project_id,  # Compatibilidad
                    user_id=UUID(current_user.id)  # Compatibilidad
                )
                await db.commit()
                logger.info(f"📝 Evento de timeline creado para edición de prompt - Sesión: {updated_prompt.context_session_id}")
            except Exception as timeline_error:
                logger.warning(f"⚠️ Error creando evento de timeline para edición: {timeline_error}")
                # No fallar la operación principal por esto
                pass
        
        return IAPromptResponse.from_orm(updated_prompt)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando prompt {prompt_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando prompt: {str(e)}"
        )


@router.post("/prompts/{prompt_id}/execute")
async def execute_prompt(
    prompt_id: UUID,
    request: ExecutePromptRequest,
    current_user: SessionUser = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Ejecuta un prompt (original o editado) consultando a las IAs.
    Este es el paso final del flujo: generar -> editar (opcional) -> ejecutar
    """
    try:
        logger.info(f"🚀 Ejecutando prompt {prompt_id} - Usar versión editada: {request.use_edited_version}")
        
        # Obtener el prompt
        ia_prompt = await ia_prompt_crud.get_ia_prompt_by_id(db, prompt_id)
        if not ia_prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt no encontrado"
            )
        
        # Determinar qué prompt usar
        if request.use_edited_version and ia_prompt.edited_prompt:
            prompt_to_use = ia_prompt.edited_prompt
            logger.info(f"📝 Usando versión editada del prompt")
        else:
            prompt_to_use = ia_prompt.generated_prompt
            logger.info(f"🎯 Usando versión original del prompt")
        
        # Ejecutar consultas a las IAs
        from app.services.ai_orchestrator import AIOrchestrator
        from app.schemas.ai_response import AIProviderEnum, AIRequest
        import time
        
        # Crear instancia del orquestador
        orchestrator = AIOrchestrator()
        
        responses = {}
        providers = [AIProviderEnum.OPENAI, AIProviderEnum.ANTHROPIC]
        
        for provider in providers:
            try:
                logger.info(f"🤖 Consultando {provider.value}...")
                start_time = time.time()
                
                # Crear request para el proveedor
                ai_request = AIRequest(
                    prompt=prompt_to_use,
                    max_tokens=1200,
                    temperature=0.7,
                    project_id=str(ia_prompt.project_id),
                    user_id=str(current_user.id)
                )
                
                # Consultar al proveedor
                response = await orchestrator.generate_single_response(
                    ai_request, provider
                )
                
                processing_time = int((time.time() - start_time) * 1000)
                
                # Guardar respuesta en la base de datos
                ia_response = await ia_prompt_crud.create_ia_response(
                    db=db,
                    ia_prompt_id=ia_prompt.id,
                    provider=provider.value,
                    response_text=response.response_text if response.response_text else "Error en la respuesta",
                    status=response.status.value,
                    latency_ms=response.latency_ms,
                    error_message=response.error_message
                )
                
                responses[provider.value] = {
                    "id": str(ia_response.id),
                    "provider": provider.value,
                    "status": response.status.value,
                    "response_text": response.response_text,
                    "latency_ms": response.latency_ms,
                    "error_message": response.error_message,
                    "success": response.status.value == "success",
                    "content": response.response_text,
                    "processing_time_ms": processing_time
                }
                
                if response.status.value == "success":
                    logger.info(f"✅ {provider.value} respondió en {processing_time}ms")
                else:
                    logger.warning(f"⚠️ {provider.value} falló: {response.error_message}")
                
            except Exception as e:
                processing_time = int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0
                logger.error(f"❌ Error consultando {provider.value}: {str(e)}")
                responses[provider.value] = {
                    "provider": provider.value,
                    "status": "error",
                    "error_message": f"Error interno: {str(e)}",
                    "success": False,
                    "processing_time_ms": processing_time
                }
        
        successful_count = len([r for r in responses.values() if r.get("success", False)])
        
        # ✅ NUEVO: Crear evento de timeline para la ejecución del prompt
        if ia_prompt.context_session_id:
            try:
                await interaction_crud.create_timeline_event(
                    db=db,
                    session_id=ia_prompt.context_session_id,
                    event_type="prompt_executed",
                    content=f"Prompt ejecutado - {successful_count}/{len(providers)} IAs respondieron exitosamente",
                    event_data={
                        "prompt_id": str(ia_prompt.id),
                        "used_edited_version": request.use_edited_version and ia_prompt.edited_prompt is not None,
                        "providers_consulted": [p.value for p in providers],
                        "successful_responses": successful_count,
                        "total_providers": len(providers),
                        "responses_summary": {
                            provider: {
                                "success": resp.get("success", False),
                                "latency_ms": resp.get("latency_ms", 0),
                                "status": resp.get("status", "unknown")
                            }
                            for provider, resp in responses.items()
                        },
                        "executed_at": datetime.utcnow().isoformat()
                    },
                    project_id=ia_prompt.project_id,  # Compatibilidad
                    user_id=UUID(current_user.id)  # Compatibilidad
                )
                logger.info(f"📝 Evento de timeline creado para ejecución de prompt - Sesión: {ia_prompt.context_session_id}")
            except Exception as timeline_error:
                logger.warning(f"⚠️ Error creando evento de timeline para ejecución: {timeline_error}")
                # No fallar la operación principal por esto
                pass
        
        # Commit de todas las respuestas guardadas
        await db.commit()
        
        # Marcar prompt como ejecutado
        await ia_prompt_crud.mark_prompt_as_executed(db, prompt_id)
        
        # ✅ NUEVO: Ejecutar síntesis automática del moderador si hay respuestas exitosas
        moderator_synthesis = None
        if successful_count >= 1:  # Si al menos una IA respondió exitosamente
            try:
                logger.info(f"🔬 Ejecutando síntesis automática del moderador...")
                
                # Crear objetos StandardAIResponse para la síntesis
                from app.schemas.ai_response import StandardAIResponse, AIResponseStatus, AIProviderEnum
                
                mock_responses = []
                for provider_name, resp_data in responses.items():
                    if resp_data.get("success", False) and resp_data.get("content"):
                        # Determinar el proveedor enum
                        if provider_name.lower() == 'openai':
                            provider_enum = AIProviderEnum.OPENAI
                        elif provider_name.lower() == 'anthropic':
                            provider_enum = AIProviderEnum.ANTHROPIC
                        else:
                            continue  # Saltar proveedores desconocidos
                        
                        mock_response = StandardAIResponse(
                            response_text=resp_data["content"],
                            status=AIResponseStatus.SUCCESS,
                            ia_provider_name=provider_enum,
                            latency_ms=resp_data.get("latency_ms", 0),
                            error_message=None,
                            timestamp=datetime.utcnow()
                        )
                        mock_responses.append(mock_response)
                
                if len(mock_responses) >= 1:  # Si tenemos al menos una respuesta para sintetizar
                    # Ejecutar síntesis del moderador
                    from app.services.ai_moderator import AIModerator
                    moderator = AIModerator()
                    
                    synthesis_start = time.time()
                    synthesis_result = await moderator.synthesize_responses(mock_responses)
                    synthesis_time = int((time.time() - synthesis_start) * 1000)
                    
                    # ✅ NUEVO: Guardar el prompt del moderador en ia_prompts
                    moderator_prompt_text = moderator.get_synthesis_prompt(mock_responses)
                    moderator_prompt = await ia_prompt_crud.create_moderator_prompt(
                        db=db,
                        project_id=ia_prompt.project_id,
                        context_session_id=ia_prompt.context_session_id,
                        original_query=ia_prompt.original_query,
                        generated_prompt=moderator_prompt_text,
                        responses_to_synthesize=len(mock_responses)
                    )
                    
                    if synthesis_result and synthesis_result.synthesis_text:
                        # ✅ NUEVO: Guardar la respuesta del moderador en ia_responses
                        moderator_response = await ia_prompt_crud.create_ia_response(
                            db=db,
                            ia_prompt_id=moderator_prompt.id,
                            provider="moderator",
                            response_text=synthesis_result.synthesis_text,
                            status="success",
                            latency_ms=synthesis_time,
                            error_message=None
                        )
                        
                        moderator_synthesis = {
                            "provider": "moderator",
                            "content": synthesis_result.synthesis_text,
                            "quality": synthesis_result.quality,
                            "key_themes": synthesis_result.key_themes,
                            "recommendations": synthesis_result.recommendations,
                            "processing_time_ms": synthesis_time,
                            "success": True,
                            "status": "success",
                            "responses_synthesized": len(mock_responses),
                            "timestamp": datetime.utcnow().isoformat(),
                            "prompt_id": str(moderator_prompt.id),  # ✅ NUEVO: ID del prompt del moderador
                            "response_id": str(moderator_response.id)  # ✅ NUEVO: ID de la respuesta del moderador
                        }
                        
                        # Crear evento de timeline para la síntesis
                        if ia_prompt.context_session_id:
                            try:
                                await interaction_crud.create_timeline_event(
                                    db=db,
                                    session_id=ia_prompt.context_session_id,
                                    event_type="moderator_synthesis",
                                    content=f"Síntesis del moderador ejecutada - Calidad: {synthesis_result.quality}",
                                    event_data={
                                        "original_prompt_id": str(ia_prompt.id),  # Prompt original de las IAs
                                        "moderator_prompt_id": str(moderator_prompt.id),  # ✅ NUEVO: Prompt del moderador
                                        "moderator_response_id": str(moderator_response.id),  # ✅ NUEVO: Respuesta del moderador
                                        "synthesis_quality": synthesis_result.quality,
                                        "responses_synthesized": len(mock_responses),
                                        "key_themes_count": len(synthesis_result.key_themes),
                                        "recommendations_count": len(synthesis_result.recommendations),
                                        "synthesis_length": len(synthesis_result.synthesis_text),
                                        "processing_time_ms": synthesis_time,
                                        "synthesized_at": datetime.utcnow().isoformat()
                                    },
                                    project_id=ia_prompt.project_id,  # Compatibilidad
                                    user_id=UUID(current_user.id)  # Compatibilidad
                                )
                                await db.commit()
                                logger.info(f"📝 Evento de timeline creado para síntesis del moderador")
                            except Exception as timeline_error:
                                logger.warning(f"⚠️ Error creando evento de timeline para síntesis: {timeline_error}")
                        
                        logger.info(f"✅ Síntesis del moderador completada - Calidad: {synthesis_result.quality}, Tiempo: {synthesis_time}ms")
                        
                        # ✅ NUEVO: Finalizar la sesión agregando la síntesis al contexto acumulado
                        if ia_prompt.context_session_id:
                            try:
                                from app.crud import session as session_crud
                                updated_session = await session_crud.finalize_session_with_synthesis(
                                    db=db,
                                    session_id=ia_prompt.context_session_id,
                                    moderator_synthesis=synthesis_result.synthesis_text,
                                    original_query=ia_prompt.original_query
                                )
                                if updated_session:
                                    logger.info(f"✅ Sesión finalizada con síntesis - ID: {ia_prompt.context_session_id}, Status: {updated_session.status}")
                                    
                                    # Crear evento de timeline para el cierre de sesión
                                    await interaction_crud.create_timeline_event(
                                        db=db,
                                        session_id=ia_prompt.context_session_id,
                                        event_type="session_completed",
                                        content=f"Sesión completada con síntesis del moderador",
                                        event_data={
                                            "original_prompt_id": str(ia_prompt.id),
                                            "moderator_prompt_id": str(moderator_prompt.id),
                                            "final_query": ia_prompt.original_query,
                                            "context_length": len(updated_session.accumulated_context),
                                            "synthesis_included": True,
                                            "completed_at": datetime.utcnow().isoformat()
                                        },
                                        project_id=ia_prompt.project_id,
                                        user_id=UUID(current_user.id)
                                    )
                                    await db.commit()
                                    logger.info(f"📝 Evento de timeline creado para cierre de sesión")
                                else:
                                    logger.warning(f"⚠️ No se pudo finalizar la sesión {ia_prompt.context_session_id}")
                            except Exception as session_error:
                                logger.error(f"❌ Error finalizando sesión: {session_error}")
                                # No fallar la operación principal por esto
                    else:
                        logger.warning("⚠️ La síntesis del moderador no produjo resultados")
                        moderator_synthesis = {
                            "provider": "moderator",
                            "error": "No se pudo generar síntesis",
                            "success": False,
                            "status": "error",
                            "processing_time_ms": synthesis_time,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                else:
                    logger.warning("⚠️ No hay suficientes respuestas exitosas para síntesis")
                    
            except Exception as synthesis_error:
                logger.error(f"❌ Error en síntesis automática: {synthesis_error}")
                moderator_synthesis = {
                    "provider": "moderator",
                    "error": f"Error en síntesis: {str(synthesis_error)}",
                    "success": False,
                    "status": "error",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # Preparar respuesta incluyendo la síntesis del moderador
        response_data = {
            "prompt_id": str(prompt_id),
            "prompt_used": prompt_to_use,
            "used_edited_version": request.use_edited_version,
            "responses": responses,
            "moderator_synthesis": moderator_synthesis,  # ✅ NUEVO: Incluir síntesis
            "successful_responses": successful_count,
            "total_responses": len(responses),
            "session_completed": moderator_synthesis and moderator_synthesis.get("success", False),  # ✅ NUEVO: Estado de sesión
            "context_session_id": str(ia_prompt.context_session_id) if ia_prompt.context_session_id else None,  # ✅ NUEVO: ID de sesión
            "executed_at": datetime.utcnow().isoformat()
        }
        
        synthesis_status = "con síntesis" if moderator_synthesis and moderator_synthesis.get("success") else "sin síntesis"
        logger.info(f"✅ Prompt ejecutado - {successful_count}/{len(responses)} respuestas exitosas, {synthesis_status}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error ejecutando prompt {prompt_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ejecutando prompt: {str(e)}"
        )


@router.get("/projects/{project_id}/prompts")
async def get_project_prompts(
    project_id: UUID,
    current_user: SessionUser = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtener todos los prompts de un proyecto (IAs y Moderador)
    """
    try:
        logger.info(f"📋 Obteniendo prompts del proyecto {project_id}")
        
        # Obtener todos los prompts clasificados
        all_prompts = await ia_prompt_crud.get_all_prompts_by_project_with_type(
            db=db,
            project_id=project_id,
            limit=100
        )
        
        # Separar por tipo
        ai_prompts = [p for p in all_prompts if not p["is_moderator"]]
        moderator_prompts = [p for p in all_prompts if p["is_moderator"]]
        
        response_data = {
            "project_id": str(project_id),
            "total_prompts": len(all_prompts),
            "ai_prompts": {
                "count": len(ai_prompts),
                "prompts": ai_prompts
            },
            "moderator_prompts": {
                "count": len(moderator_prompts),
                "prompts": moderator_prompts
            },
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Prompts obtenidos - {len(ai_prompts)} IAs, {len(moderator_prompts)} Moderador")
        
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo prompts del proyecto {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo prompts: {str(e)}"
        )


@router.get("/sessions/{session_id}/status")
async def get_session_status(
    session_id: UUID,
    current_user: SessionUser = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtener el estado y contexto acumulado de una sesión
    """
    try:
        logger.info(f"📋 Obteniendo estado de sesión {session_id}")
        
        # Obtener la sesión
        from app.crud import session as session_crud
        session = await session_crud.get_session(db, session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada"
            )
        
        # Obtener eventos del timeline
        timeline_events = await interaction_crud.get_session_timeline(db, session_id)
        
        # Contar eventos por tipo
        event_counts = {}
        for event in timeline_events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        response_data = {
            "session_id": str(session_id),
            "status": session.status,
            "accumulated_context": session.accumulated_context,
            "context_length": len(session.accumulated_context),
            "final_question": session.final_question,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "finished_at": session.finished_at.isoformat() if session.finished_at else None,
            "timeline_events": {
                "total_events": len(timeline_events),
                "event_counts": event_counts,
                "latest_events": [
                    {
                        "event_type": event.event_type,
                        "content": event.content,
                        "created_at": event.created_at.isoformat()
                    }
                    for event in timeline_events[-5:]  # Últimos 5 eventos
                ]
            }
        }
        
        logger.info(f"✅ Estado de sesión obtenido - Status: {session.status}, Eventos: {len(timeline_events)}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado de sesión {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estado de sesión: {str(e)}"
        )


# Función auxiliar para guardar respuestas de IA con sus prompts
async def save_ia_response_with_prompt(
    db: AsyncSession,
    project_id: UUID,
    provider: str,
    prompt_text: str,
    response_text: str,
    latency_ms: int,
    user_question: str,
    error_message: str = None
) -> None:
    """
    Guarda una respuesta de IA junto con su prompt en la base de datos.
    """
    try:
        from app.models.models import IAResponse
        from uuid import uuid4
        from datetime import datetime
        
        # Crear registro de respuesta IA con prompt
        ia_response = IAResponse(
            id=uuid4(),
            project_id=project_id,
            prompt_text=prompt_text,
            ia_provider_name=provider,
            raw_response_text=response_text or "",
            latency_ms=latency_ms,
            error_message=error_message,
            received_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(ia_response)
        await db.commit()
        
        logger.info(f"💾 Respuesta de {provider} guardada en BD con prompt (longitud: {len(prompt_text)} chars)")
        
    except Exception as e:
        logger.error(f"❌ Error guardando respuesta de {provider} en BD: {e}")
        await db.rollback()
        # No re-raise la excepción para no romper el flujo principal




@router.get(
    "/projects/{project_id}/context-sessions-summary",
    response_model=Dict[str, Any],
    summary="Obtener resumen de sesiones de contexto por proyecto",
    description="Obtiene un resumen de todas las sesiones de contexto organizadas por chat para un proyecto"
)
async def get_project_context_sessions_summary(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """
    Obtiene un resumen de todas las sesiones de contexto de un proyecto organizadas por chat.
    Este endpoint es para mostrar información general, no para navegar sesiones específicas.
    """
    try:
        user_id = UUID(current_user.id)
        
        # Obtener todos los chats del proyecto del usuario
        chats = await chat_crud.get_chats_by_project(db, project_id)
        user_chats = [chat for chat in chats if chat.user_id == user_id]
        
        chats_with_sessions = []
        total_sessions = 0
        active_sessions = 0
        
        for chat in user_chats:
            # Obtener sesiones del chat
            sessions = await session_crud.get_sessions_by_chat(db, chat.id)
            
            sessions_data = []
            for session in sessions:
                timeline_count = await interaction_crud.count_interactions_by_session(db, session.id)
                
                session_summary = {
                    "id": session.id,
                    "order_index": session.order_index,
                    "status": session.status,
                    "context_length": len(session.accumulated_context),
                    "timeline_events_count": timeline_count,
                    "started_at": session.started_at,
                    "finished_at": session.finished_at,
                    "has_synthesis": "🔬 Síntesis del Moderador" in (session.accumulated_context or ""),
                    "is_active": session.status == "active"
                }
                sessions_data.append(session_summary)
                total_sessions += 1
                if session.status == "active":
                    active_sessions += 1
            
            if sessions_data:  # Solo incluir chats que tienen sesiones
                chats_with_sessions.append({
                    "chat_id": chat.id,
                    "chat_title": chat.title,
                    "sessions_count": len(sessions_data),
                    "sessions": sessions_data
                })
        
        return {
            "project_id": project_id,
            "chats_with_sessions": chats_with_sessions,
            "total_chats": len(chats_with_sessions),
            "total_sessions": total_sessions,
            "active_sessions": active_sessions
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo resumen de sesiones del proyecto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo resumen de sesiones: {str(e)}"
        )

 