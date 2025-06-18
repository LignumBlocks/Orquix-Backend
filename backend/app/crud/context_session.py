import json
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import InteractionEvent
from app.models.context_session import ContextMessage, ContextSession, ContextSessionSummary

logger = logging.getLogger(__name__)


async def create_context_session(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    initial_message: Optional[str] = None
) -> InteractionEvent:
    """
    Crea una nueva sesión de construcción de contexto usando InteractionEvent.
    
    Args:
        db: Sesión de base de datos
        project_id: ID del proyecto
        user_id: ID del usuario
        initial_message: Mensaje inicial opcional
        
    Returns:
        Nueva sesión de contexto
    """
    # Crear historial inicial
    conversation_history = []
    if initial_message:
        conversation_history.append({
            "role": "user",
            "content": initial_message,
            "timestamp": datetime.utcnow().isoformat(),
            "message_type": "information"
        })
    
    # Crear InteractionEvent para construcción de contexto
    session = InteractionEvent(
        id=uuid4(),
        project_id=project_id,
        user_id=user_id,
        user_prompt_text=initial_message or "Iniciando construcción de contexto",
        context_used_summary="",  # Contexto acumulado
        ai_responses_json=json.dumps(conversation_history),  # Historial conversacional
        interaction_type="context_building",
        session_status="active",
        context_used=True,
        created_at=datetime.utcnow()
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    logger.info(f"✅ Nueva sesión de contexto creada: {session.id}")
    return session


async def get_context_session(
    db: AsyncSession,
    session_id: UUID
) -> Optional[InteractionEvent]:
    """
    Obtiene una sesión de contexto por ID.
    
    Args:
        db: Sesión de base de datos
        session_id: ID de la sesión
        
    Returns:
        Sesión de contexto o None si no existe
    """
    logger.info(f"🔍 Buscando sesión en BD: {session_id} (tipo: {type(session_id)})")
    query = select(InteractionEvent).where(
        InteractionEvent.id == session_id,
        InteractionEvent.interaction_type == "context_building",
        InteractionEvent.deleted_at.is_(None)
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    logger.info(f"📋 Resultado de búsqueda: {session is not None}")
    if session:
        logger.info(f"📋 Sesión encontrada: {session.id}, type={session.interaction_type}, status={session.session_status}")
    return session


async def get_active_session_for_project(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID
) -> Optional[InteractionEvent]:
    """
    Obtiene la sesión activa para un proyecto y usuario.
    
    Args:
        db: Sesión de base de datos
        project_id: ID del proyecto
        user_id: ID del usuario
        
    Returns:
        Sesión activa o None si no existe
    """
    query = select(InteractionEvent).where(
        InteractionEvent.project_id == project_id,
        InteractionEvent.user_id == user_id,
        InteractionEvent.interaction_type == "context_building",
        InteractionEvent.session_status == "active",
        InteractionEvent.deleted_at.is_(None)
    ).order_by(InteractionEvent.updated_at.desc())
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_context_session(
    db: AsyncSession,
    session: InteractionEvent,
    new_message: ContextMessage,
    updated_context: str
) -> InteractionEvent:
    """
    Actualiza una sesión de contexto con un nuevo mensaje.
    
    Args:
        db: Sesión de base de datos
        session: Sesión a actualizar
        new_message: Nuevo mensaje a agregar
        updated_context: Contexto actualizado
        
    Returns:
        Sesión actualizada
    """
    # Parsear historial actual
    try:
        conversation_history = json.loads(session.ai_responses_json or "[]")
    except (json.JSONDecodeError, TypeError):
        conversation_history = []
    
    # Agregar nuevo mensaje
    conversation_history.append({
        "role": new_message.role,
        "content": new_message.content,
        "timestamp": new_message.timestamp.isoformat(),
        "message_type": new_message.message_type
    })
    
    # Actualizar sesión
    session.ai_responses_json = json.dumps(conversation_history)
    session.context_used_summary = updated_context
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    
    logger.info(f"📝 Sesión de contexto actualizada: {session.id}")
    return session


async def finalize_context_session(
    db: AsyncSession,
    session_id: UUID
) -> Optional[InteractionEvent]:
    """
    Finaliza una sesión de contexto (la marca como completada).
    
    Args:
        db: Sesión de base de datos
        session_id: ID de la sesión
        
    Returns:
        Sesión finalizada o None si no existe
    """
    session = await get_context_session(db, session_id)
    if not session:
        return None
    
    session.session_status = "completed"
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    
    logger.info(f"🏁 Sesión de contexto finalizada: {session.id}")
    return session


async def get_project_context_sessions(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    limit: int = 10
) -> List[ContextSessionSummary]:
    """
    Obtiene las sesiones de contexto de un proyecto.
    
    Args:
        db: Sesión de base de datos
        project_id: ID del proyecto
        user_id: ID del usuario
        limit: Límite de resultados
        
    Returns:
        Lista de resúmenes de sesiones
    """
    query = select(InteractionEvent).where(
        InteractionEvent.project_id == project_id,
        InteractionEvent.user_id == user_id,
        InteractionEvent.interaction_type == "context_building",
        InteractionEvent.deleted_at.is_(None)
    ).order_by(InteractionEvent.updated_at.desc()).limit(limit)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # Convertir a resúmenes
    summaries = []
    for session in sessions:
        try:
            conversation_history = json.loads(session.ai_responses_json or "[]")
            messages_count = len(conversation_history)
        except (json.JSONDecodeError, TypeError):
            messages_count = 0
        
        summaries.append(ContextSessionSummary(
            id=session.id,
            project_id=session.project_id,
            accumulated_context=session.context_used_summary or "",
            messages_count=messages_count,
            is_active=(session.session_status == "active"),
            created_at=session.created_at,
            last_activity=session.updated_at
        ))
    
    return summaries


def convert_interaction_to_context_session(interaction: InteractionEvent) -> ContextSession:
    """
    Convierte un InteractionEvent a modelo ContextSession.
    
    Args:
        interaction: InteractionEvent de tipo context_building
        
    Returns:
        Sesión en formato ContextSession
    """
    try:
        conversation_data = json.loads(interaction.ai_responses_json or "[]")
        conversation_history = [
            ContextMessage(
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                timestamp=datetime.fromisoformat(msg.get("timestamp", datetime.utcnow().isoformat())),
                message_type=msg.get("message_type")
            )
            for msg in conversation_data
        ]
    except (json.JSONDecodeError, TypeError):
        conversation_history = []
    
    return ContextSession(
        id=interaction.id,
        project_id=interaction.project_id,
        user_id=interaction.user_id,
        conversation_history=conversation_history,
        accumulated_context=interaction.context_used_summary or "",
        is_active=(interaction.session_status == "active"),
        created_at=interaction.created_at,
        updated_at=interaction.updated_at
    ) 