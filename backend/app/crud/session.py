from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
import logging

from app.models.models import Session

logger = logging.getLogger(__name__)


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
    
    # ✅ NUEVO: Herencia de contexto - si no se proporciona contexto y hay sesión anterior
    if not accumulated_context and previous_session and previous_session.accumulated_context:
        accumulated_context = previous_session.accumulated_context
        print(f"🔄 Heredando contexto de sesión anterior: {len(accumulated_context)} caracteres")
    
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


async def finalize_session_with_synthesis(
    db: AsyncSession,
    session_id: UUID,
    moderator_synthesis: str,
    original_query: str,
    create_next_session: bool = True
) -> Optional[Session]:
    """Finalizar una sesión agregando la síntesis del moderador al contexto acumulado."""
    session = await get_session(db, session_id)
    if not session:
        return None
    
    # Agregar la síntesis del moderador al contexto acumulado
    synthesis_section = f"\n\n## 🔬 Síntesis del Moderador\n\n{moderator_synthesis}\n\n---\n"
    updated_context = session.accumulated_context + synthesis_section
    
    # Actualizar la sesión con el nuevo contexto y marcarla como completada
    session.accumulated_context = updated_context
    session.final_question = original_query
    session.status = "completed"
    session.finished_at = datetime.utcnow()
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    
    # Crear automáticamente una nueva sesión activa que herede el contexto
    if create_next_session:
        try:
            new_session = await create_session(
                db=db,
                chat_id=session.chat_id,
                user_id=session.user_id,
                accumulated_context=updated_context,  # Heredar el contexto con síntesis
                status="active"
            )
            
            # Establecer la relación con la sesión anterior
            new_session.previous_session_id = session.id
            await db.commit()
            await db.refresh(new_session)
            
            logger.info(f"✅ Nueva sesión activa creada: {new_session.id} (hereda contexto de {session.id})")
            
        except Exception as e:
            logger.error(f"❌ Error creando nueva sesión activa: {e}")
            # No fallar si no se puede crear la nueva sesión
    
    return session


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


async def get_or_create_active_session(
    db: AsyncSession,
    chat_id: UUID,
    user_id: UUID
) -> Session:
    """Obtener la sesión activa de un chat o crear una nueva si no existe."""
    # Primero intentar obtener una sesión activa existente
    active_session = await get_active_session(db, chat_id)
    
    if active_session:
        logger.info(f"📋 Sesión activa encontrada: {active_session.id}")
        return active_session
    
    # No hay sesión activa, crear una nueva
    logger.info(f"🆕 No hay sesión activa, creando nueva para chat {chat_id}")
    
    # Obtener la última sesión para heredar contexto
    last_session = await get_last_session(db, chat_id)
    inherited_context = ""
    
    if last_session and last_session.accumulated_context:
        inherited_context = last_session.accumulated_context
        logger.info(f"🔄 Heredando contexto de sesión anterior: {len(inherited_context)} caracteres")
    
    # Crear nueva sesión activa
    new_session = await create_session(
        db=db,
        chat_id=chat_id,
        user_id=user_id,
        accumulated_context=inherited_context,
        status="active"
    )
    
    logger.info(f"✅ Nueva sesión activa creada: {new_session.id}")
    return new_session 