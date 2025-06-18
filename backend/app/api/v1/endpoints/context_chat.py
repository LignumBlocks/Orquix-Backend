import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.auth import SessionUser
from app.crud import context_session as context_crud
from app.models.context_session import (
    ContextChatRequest,
    ContextChatResponse,
    ContextFinalizeRequest,
    ContextMessage,
    ContextSession,
    ContextSessionSummary
)
from app.services.context_builder import context_builder_service

logger = logging.getLogger(__name__)

router = APIRouter()

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
            db_session = await context_crud.get_context_session(db, session_uuid)
            logger.info(f"📋 Sesión encontrada: {db_session is not None}")
            if db_session:
                logger.info(f"📋 Sesión details: project_id={db_session.project_id}, user_id={db_session.user_id}, status={db_session.session_status}")
                logger.info(f"📋 Comparación project_id: {db_session.project_id} == {project_id} -> {db_session.project_id == project_id}")
                logger.info(f"📋 Comparación user_id: {db_session.user_id} == {user_id} -> {db_session.user_id == user_id}")
            if not db_session or db_session.project_id != project_id or db_session.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sesión de contexto no encontrada"
                )
        else:
            # Crear nueva sesión
            db_session = await context_crud.create_context_session(
                db=db,
                project_id=project_id,
                user_id=user_id,
                initial_message=request.user_message
            )
        
        # Convertir a modelo Pydantic para trabajar con el servicio
        session = context_crud.convert_interaction_to_context_session(db_session)
        
        # Procesar mensaje con GPT-3.5
        response = await context_builder_service.process_user_message(
            user_message=request.user_message,
            conversation_history=session.conversation_history,
            current_context=session.accumulated_context
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
        await context_crud.update_context_session(
            db=db,
            session=db_session,
            new_message=user_message,
            updated_context=response.accumulated_context
        )
        
        # Actualizar sesión con respuesta de la IA
        await context_crud.update_context_session(
            db=db,
            session=db_session,
            new_message=ai_message,
            updated_context=response.accumulated_context
        )
        
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
        sessions = await context_crud.get_project_context_sessions(
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
        db_session = await context_crud.get_context_session(db, session_id)
        if not db_session or db_session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión de contexto no encontrada"
            )
        
        session = context_crud.convert_interaction_to_context_session(db_session)
        return session
        
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
        db_session = await context_crud.get_context_session(db, session_id)
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
        await context_crud.finalize_context_session(db, session_id)
        
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
        db_session = await context_crud.get_active_session_for_project(
            db=db,
            project_id=project_id,
            user_id=user_id
        )
        
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay sesión de contexto activa"
            )
        
        session = context_crud.convert_interaction_to_context_session(db_session)
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo sesión activa: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo sesión activa: {str(e)}"
        ) 