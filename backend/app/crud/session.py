from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import Session


async def create_session(
    db: AsyncSession,
    chat_id: UUID,
    user_id: Optional[UUID],
    accumulated_context: str = "",
    final_question: Optional[str] = None,
    status: str = "active"
) -> Session:
    """Crear una nueva sesión."""
    # Obtener el order_index siguiente
    statement = select(func.max(Session.order_index)).where(
        Session.chat_id == chat_id,
        Session.deleted_at.is_(None)
    )
    result = await db.exec(statement)
    max_order = result.first() or 0
    
    # Obtener la sesión anterior si existe
    previous_session = await get_last_session(db, chat_id)
    
    session = Session(
        chat_id=chat_id,
        previous_session_id=previous_session.id if previous_session else None,
        user_id=user_id,
        accumulated_context=accumulated_context,
        final_question=final_question,
        status=status,
        order_index=max_order + 1
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: UUID) -> Optional[Session]:
    """Obtener una sesión por ID."""
    from app.models.models import Chat
    statement = select(Session).join(Chat).where(
        Session.id == session_id,
        Session.deleted_at.is_(None)
    )
    result = await db.exec(statement)
    session = result.first()
    
    # Cargar la relación con el chat manualmente si es necesario
    if session:
        chat_statement = select(Chat).where(Chat.id == session.chat_id)
        chat_result = await db.exec(chat_statement)
        session.chat = chat_result.first()
    
    return session


async def get_sessions_by_chat(
    db: AsyncSession,
    chat_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Session]:
    """Obtener todas las sesiones de un chat."""
    statement = select(Session).where(
        Session.chat_id == chat_id,
        Session.deleted_at.is_(None)
    ).order_by(Session.order_index.asc()).offset(skip).limit(limit)
    
    result = await db.exec(statement)
    return result.all()


async def get_last_session(db: AsyncSession, chat_id: UUID) -> Optional[Session]:
    """Obtener la última sesión de un chat."""
    statement = select(Session).where(
        Session.chat_id == chat_id,
        Session.deleted_at.is_(None)
    ).order_by(Session.order_index.desc()).limit(1)
    
    result = await db.exec(statement)
    return result.first()


async def get_active_session(db: AsyncSession, chat_id: UUID) -> Optional[Session]:
    """Obtener la sesión activa de un chat."""
    statement = select(Session).where(
        Session.chat_id == chat_id,
        Session.status == "active",
        Session.deleted_at.is_(None)
    ).order_by(Session.order_index.desc()).limit(1)
    
    result = await db.exec(statement)
    return result.first()


async def update_session_context(
    db: AsyncSession,
    session_id: UUID,
    accumulated_context: str
) -> Optional[Session]:
    """Actualizar el contexto acumulado de una sesión."""
    session = await get_session(db, session_id)
    if not session:
        return None
    
    session.accumulated_context = accumulated_context
    session.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    return session


async def update_session_status(
    db: AsyncSession,
    session_id: UUID,
    status: str,
    final_question: Optional[str] = None
) -> Optional[Session]:
    """Actualizar el estado de una sesión."""
    session = await get_session(db, session_id)
    if not session:
        return None
    
    session.status = status
    if final_question is not None:
        session.final_question = final_question
    
    if status == "completed":
        session.finished_at = datetime.utcnow()
    
    session.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    return session


async def complete_session(
    db: AsyncSession,
    session_id: UUID,
    final_question: str
) -> Optional[Session]:
    """Completar una sesión."""
    return await update_session_status(db, session_id, "completed", final_question)


async def delete_session(db: AsyncSession, session_id: UUID) -> bool:
    """Eliminar una sesión (soft delete)."""
    session = await get_session(db, session_id)
    if not session:
        return False
    
    # Actualizar sesiones posteriores para que apunten al anterior
    later_sessions_statement = select(Session).where(
        Session.chat_id == session.chat_id,
        Session.order_index > session.order_index,
        Session.deleted_at.is_(None)
    )
    result = await db.exec(later_sessions_statement)
    later_sessions = result.all()
    
    for later_session in later_sessions:
        if later_session.previous_session_id == session_id:
            later_session.previous_session_id = session.previous_session_id
    
    # Soft delete de la sesión
    session.deleted_at = datetime.utcnow()
    await db.commit()
    return True


async def get_session_with_context_chain(
    db: AsyncSession,
    session_id: UUID
) -> Optional[List[Session]]:
    """Obtener una sesión con toda su cadena de contexto anterior."""
    sessions = []
    current_session = await get_session(db, session_id)
    
    while current_session:
        sessions.insert(0, current_session)  # Insertar al inicio para mantener orden
        if current_session.previous_session_id:
            current_session = await get_session(db, current_session.previous_session_id)
        else:
            break
    
    return sessions if sessions else None


async def count_sessions_by_chat(db: AsyncSession, chat_id: UUID) -> int:
    """Contar sesiones de un chat."""
    statement = select(Session).where(
        Session.chat_id == chat_id,
        Session.deleted_at.is_(None)
    )
    result = await db.exec(statement)
    return len(result.all())


async def get_sessions_by_status(
    db: AsyncSession,
    chat_id: UUID,
    status: str
) -> List[Session]:
    """Obtener sesiones por estado."""
    statement = select(Session).where(
        Session.chat_id == chat_id,
        Session.status == status,
        Session.deleted_at.is_(None)
    ).order_by(Session.order_index.asc())
    
    result = await db.exec(statement)
    return result.all() 