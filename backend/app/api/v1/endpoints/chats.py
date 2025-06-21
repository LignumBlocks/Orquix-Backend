import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.auth import SessionUser
from app.schemas.chat import (
    ChatCreate, ChatCreateRequest, ChatUpdate, ChatResponse, ChatSummary, 
    ChatWithSessions, ChatStats, ChatListResponse
)
from app.schemas.session import (
    SessionCreate, SessionCreateRequest, SessionUpdate, SessionResponse, SessionSummary,
    SessionWithContext, SessionContextChain, SessionStats,
    SessionStatusUpdate, SessionContextUpdate, SessionListResponse
)
from app.crud import chat as chat_crud
from app.crud import session as session_crud
from app.crud import interaction as interaction_crud
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


# =============================================================================
# ENDPOINTS DE CHAT
# =============================================================================

@router.post(
    "/projects/{project_id}/chats",
    response_model=ChatResponse,
    summary="Crear nuevo chat",
    description="Crea un nuevo hilo conversacional en un proyecto"
)
async def create_chat(
    project_id: UUID,
    request: ChatCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Crear un nuevo chat en un proyecto."""
    try:
        user_id = UUID(current_user.id)
        
        chat = await chat_crud.create_chat(
            db=db,
            project_id=project_id,
            user_id=user_id,
            title=request.title,
            is_archived=request.is_archived
        )
        
        logger.info(f"💬 Chat creado: {chat.id} - {chat.title}")
        return chat
        
    except Exception as e:
        logger.error(f"Error creando chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating chat"
        )


@router.get(
    "/projects/{project_id}/chats",
    response_model=ChatListResponse,
    summary="Listar chats del proyecto",
    description="Obtiene todos los chats de un proyecto con paginación"
)
async def get_project_chats(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    include_archived: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Obtener chats de un proyecto."""
    try:
        chats = await chat_crud.get_chats_by_project(
            db=db,
            project_id=project_id,
            skip=skip,
            limit=limit,
            include_archived=include_archived
        )
        
        total = await chat_crud.count_chats_by_project(
            db=db,
            project_id=project_id,
            include_archived=include_archived
        )
        
        # Convertir a ChatSummary con información adicional
        chat_summaries = []
        for chat in chats:
            sessions_count = await session_crud.count_sessions_by_chat(db, chat.id)
            
            # Obtener última actividad
            last_session = await session_crud.get_last_session(db, chat.id)
            last_activity = last_session.started_at if last_session else None
            
            chat_summary = ChatSummary(
                id=chat.id,
                title=chat.title,
                is_archived=chat.is_archived,
                created_at=chat.created_at,
                sessions_count=sessions_count,
                last_activity=last_activity
            )
            chat_summaries.append(chat_summary)
        
        return ChatListResponse(
            chats=chat_summaries,
            total=total,
            page=skip // limit + 1,
            per_page=limit,
            has_next=(skip + limit) < total
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo chats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving chats"
        )


@router.get(
    "/chats/{chat_id}",
    response_model=ChatResponse,
    summary="Obtener chat específico",
    description="Obtiene un chat específico por ID"
)
async def get_chat(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Obtener un chat específico."""
    chat = await chat_crud.get_chat(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    return chat


@router.put(
    "/chats/{chat_id}",
    response_model=ChatResponse,
    summary="Actualizar chat",
    description="Actualiza el título o estado de archivado de un chat"
)
async def update_chat(
    chat_id: UUID,
    request: ChatUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Actualizar un chat."""
    chat = await chat_crud.update_chat(
        db=db,
        chat_id=chat_id,
        title=request.title,
        is_archived=request.is_archived
    )
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    logger.info(f"💬 Chat actualizado: {chat.id}")
    return chat


@router.delete(
    "/chats/{chat_id}",
    summary="Eliminar chat",
    description="Elimina un chat (soft delete)"
)
async def delete_chat(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Eliminar un chat."""
    success = await chat_crud.delete_chat(db, chat_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    logger.info(f"🗑️ Chat eliminado: {chat_id}")
    return {"message": "Chat deleted successfully"}


@router.get(
    "/chats/{chat_id}/with-sessions",
    response_model=ChatWithSessions,
    summary="Chat con sesiones",
    description="Obtiene un chat con todas sus sesiones"
)
async def get_chat_with_sessions(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Obtener chat con todas sus sesiones."""
    chat = await chat_crud.get_chat(db, chat_id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    sessions = await session_crud.get_sessions_by_chat(db, chat_id)
    
    # Convertir a dict para evitar problemas de serialización
    sessions_data = [session.model_dump() for session in sessions]
    
    return ChatWithSessions(
        **chat.model_dump(),
        sessions=sessions_data
    )


# =============================================================================
# ENDPOINTS DE SESSION
# =============================================================================

@router.post(
    "/chats/{chat_id}/sessions",
    response_model=SessionResponse,
    summary="Crear nueva sesión",
    description="Crea una nueva sesión en un chat"
)
async def create_session(
    chat_id: UUID,
    request: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Crear una nueva sesión en un chat."""
    try:
        user_id = UUID(current_user.id)
        
        # Verificar que el chat existe
        chat = await chat_crud.get_chat(db, chat_id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        session = await session_crud.create_session(
            db=db,
            chat_id=chat_id,
            user_id=user_id,
            accumulated_context=request.accumulated_context,
            final_question=request.final_question,
            status=request.status
        )
        
        logger.info(f"🔄 Sesión creada: {session.id} en chat {chat_id}")
        return session
        
    except Exception as e:
        logger.error(f"Error creando sesión: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating session"
        )


@router.get(
    "/chats/{chat_id}/sessions",
    response_model=SessionListResponse,
    summary="Listar sesiones del chat",
    description="Obtiene todas las sesiones de un chat"
)
async def get_chat_sessions(
    chat_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Obtener sesiones de un chat."""
    sessions = await session_crud.get_sessions_by_chat(
        db=db,
        chat_id=chat_id,
        skip=skip,
        limit=limit
    )
    
    total = await session_crud.count_sessions_by_chat(db, chat_id)
    
    # Convertir a SessionSummary con información adicional
    session_summaries = []
    for session in sessions:
        interactions_count = await interaction_crud.count_interactions_by_session(db, session.id)
        
        session_summary = SessionSummary(
            id=session.id,
            order_index=session.order_index,
            status=session.status,
            started_at=session.started_at,
            finished_at=session.finished_at,
            context_length=len(session.accumulated_context),
            interactions_count=interactions_count,
            has_final_question=session.final_question is not None
        )
        session_summaries.append(session_summary)
    
    return SessionListResponse(
        sessions=session_summaries,
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        has_next=(skip + limit) < total
    )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Obtener sesión específica",
    description="Obtiene una sesión específica por ID"
)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Obtener una sesión específica."""
    session = await session_crud.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return session


@router.put(
    "/sessions/{session_id}/context",
    response_model=SessionResponse,
    summary="Actualizar contexto de sesión",
    description="Actualiza el contexto acumulado de una sesión"
)
async def update_session_context(
    session_id: UUID,
    request: SessionContextUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Actualizar el contexto de una sesión."""
    session = await session_crud.update_session_context(
        db=db,
        session_id=session_id,
        accumulated_context=request.accumulated_context
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    logger.info(f"🔄 Contexto de sesión actualizado: {session_id}")
    return session


@router.put(
    "/sessions/{session_id}/status",
    response_model=SessionResponse,
    summary="Actualizar estado de sesión",
    description="Actualiza el estado de una sesión"
)
async def update_session_status(
    session_id: UUID,
    request: SessionStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Actualizar el estado de una sesión."""
    session = await session_crud.update_session_status(
        db=db,
        session_id=session_id,
        status=request.status,
        final_question=request.final_question
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    logger.info(f"🔄 Estado de sesión actualizado: {session_id} -> {request.status}")
    return session


@router.get(
    "/chats/{chat_id}/active-session",
    response_model=SessionResponse,
    summary="Obtener sesión activa",
    description="Obtiene la sesión activa de un chat"
)
async def get_active_session(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Obtener la sesión activa de un chat."""
    session = await session_crud.get_active_session(db, chat_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session found"
        )
    return session


@router.get(
    "/sessions/{session_id}/context-chain",
    response_model=SessionContextChain,
    summary="Obtener cadena de contexto",
    description="Obtiene la cadena completa de contexto de una sesión"
)
async def get_session_context_chain(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Obtener la cadena de contexto de una sesión."""
    context_chain = await session_crud.get_session_with_context_chain(db, session_id)
    
    if not context_chain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    total_context_length = sum(len(s.accumulated_context) for s in context_chain)
    
    return SessionContextChain(
        session_id=session_id,
        context_chain=context_chain,
        total_context_length=total_context_length,
        sessions_count=len(context_chain)
    )


@router.delete(
    "/sessions/{session_id}",
    summary="Eliminar sesión",
    description="Elimina una sesión (soft delete) y reconecta las sesiones posteriores"
)
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """Eliminar una sesión."""
    success = await session_crud.delete_session(db, session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    logger.info(f"🗑️ Sesión eliminada: {session_id}")
    return {"message": "Session deleted successfully"}


@router.get(
    "/chats/{chat_id}/sessions/detailed",
    response_model=Dict[str, Any],
    summary="Obtener sesiones detalladas del chat",
    description="Obtiene todas las sesiones de un chat con información detallada para el sidebar"
)
async def get_chat_sessions_detailed(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """
    Obtener sesiones de un chat con información detallada para mostrar en el sidebar.
    Incluye contexto, eventos de timeline, y estado de síntesis.
    """
    try:
        # Verificar que el chat existe y pertenece al usuario
        chat = await chat_crud.get_chat(db, chat_id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        user_id = UUID(current_user.id)
        if chat.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a este chat"
            )
        
        # Obtener todas las sesiones del chat
        sessions = await session_crud.get_sessions_by_chat(db, chat_id)
        
        sessions_detailed = []
        active_session_id = None
        
        for session in sessions:
            # Contar eventos de timeline
            timeline_count = await interaction_crud.count_interactions_by_session(db, session.id)
            
            session_data = {
                "id": session.id,
                "order_index": session.order_index,
                "status": session.status,
                "accumulated_context": session.accumulated_context,
                "context_length": len(session.accumulated_context),
                "final_question": session.final_question,
                "started_at": session.started_at,
                "finished_at": session.finished_at,
                "updated_at": session.updated_at,
                "timeline_events_count": timeline_count,
                "is_active": session.status == "active",
                "has_synthesis": "🔬 Síntesis del Moderador" in (session.accumulated_context or "")
            }
            
            sessions_detailed.append(session_data)
            
            # Marcar sesión activa
            if session.status == "active":
                active_session_id = session.id
        
        # Ordenar por order_index (más reciente primero)
        sessions_detailed.sort(key=lambda s: s["order_index"], reverse=True)
        
        return {
            "chat_id": chat_id,
            "chat_title": chat.title,
            "sessions": sessions_detailed,
            "total_sessions": len(sessions_detailed),
            "active_session_id": active_session_id,
            "sessions_with_synthesis": len([s for s in sessions_detailed if s["has_synthesis"]]),
            "completed_sessions": len([s for s in sessions_detailed if s["status"] == "completed"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo sesiones detalladas del chat {chat_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo sesiones detalladas: {str(e)}"
        ) 