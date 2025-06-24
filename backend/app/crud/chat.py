from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import logging

from app.models.models import Chat, Session, InteractionEvent

logger = logging.getLogger(__name__)


async def create_chat(
    db: AsyncSession,
    project_id: UUID,
    user_id: Optional[UUID],
    title: str,
    is_archived: bool = False
) -> Chat:
    """Crear un nuevo chat."""
    chat = Chat(
        project_id=project_id,
        user_id=user_id,
        title=title,
        is_archived=is_archived
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


async def get_chat(db: AsyncSession, chat_id: UUID) -> Optional[Chat]:
    """Obtener un chat por ID."""
    statement = select(Chat).where(
        Chat.id == chat_id,
        Chat.deleted_at.is_(None)
    )
    result = await db.exec(statement)
    return result.first()


async def get_chats_by_project(
    db: AsyncSession, 
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = False
) -> List[Chat]:
    """Obtener todos los chats de un proyecto."""
    statement = select(Chat).where(
        Chat.project_id == project_id,
        Chat.deleted_at.is_(None)
    )
    
    if not include_archived:
        statement = statement.where(Chat.is_archived == False)
    
    statement = statement.offset(skip).limit(limit).order_by(Chat.created_at.desc())
    result = await db.exec(statement)
    return result.all()


async def get_chats_by_user(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = False
) -> List[Chat]:
    """Obtener todos los chats de un usuario."""
    statement = select(Chat).where(
        Chat.user_id == user_id,
        Chat.deleted_at.is_(None)
    )
    
    if not include_archived:
        statement = statement.where(Chat.is_archived == False)
    
    statement = statement.offset(skip).limit(limit).order_by(Chat.created_at.desc())
    result = await db.exec(statement)
    return result.all()


async def update_chat(
    db: AsyncSession,
    chat_id: UUID,
    title: Optional[str] = None,
    is_archived: Optional[bool] = None
) -> Optional[Chat]:
    """Actualizar un chat."""
    chat = await get_chat(db, chat_id)
    if not chat:
        return None
    
    if title is not None:
        chat.title = title
    if is_archived is not None:
        chat.is_archived = is_archived
    
    chat.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(chat)
    return chat


async def archive_chat(db: AsyncSession, chat_id: UUID) -> Optional[Chat]:
    """Archivar un chat."""
    return await update_chat(db, chat_id, is_archived=True)


async def unarchive_chat(db: AsyncSession, chat_id: UUID) -> Optional[Chat]:
    """Desarchivar un chat."""
    return await update_chat(db, chat_id, is_archived=False)


async def delete_chat(db: AsyncSession, chat_id: UUID) -> bool:
    """Eliminar un chat y todas sus sesiones e interacciones asociadas (soft delete en cascada)."""
    chat = await get_chat(db, chat_id)
    if not chat:
        logger.warning(f"🚫 Intento de eliminar chat inexistente: {chat_id}")
        return False
    
    logger.info(f"🗑️ Iniciando eliminación en cascada del chat: {chat_id} - '{chat.title}'")
    
    # Obtener todas las sesiones del chat
    sessions_statement = select(Session).where(
        Session.chat_id == chat_id,
        Session.deleted_at.is_(None)
    )
    sessions_result = await db.exec(sessions_statement)
    sessions = sessions_result.all()
    
    logger.info(f"📋 Encontradas {len(sessions)} sesiones para eliminar")
    
    # Para cada sesión, eliminar sus interacciones
    session_ids = [session.id for session in sessions]
    total_interactions = 0
    
    if session_ids:
        # Eliminar todas las interacciones de las sesiones (soft delete)
        interactions_statement = select(InteractionEvent).where(
            InteractionEvent.session_id.in_(session_ids),
            InteractionEvent.deleted_at.is_(None)
        )
        interactions_result = await db.exec(interactions_statement)
        interactions = interactions_result.all()
        
        total_interactions = len(interactions)
        logger.info(f"💬 Encontradas {total_interactions} interacciones para eliminar")
        
        # Marcar interacciones como eliminadas
        for interaction in interactions:
            interaction.deleted_at = datetime.utcnow()
    
    # Eliminar todas las sesiones del chat (soft delete)
    for session in sessions:
        session.deleted_at = datetime.utcnow()
    
    # Finalmente eliminar el chat (soft delete)
    chat.deleted_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"✅ Chat eliminado exitosamente: {chat_id}")
    logger.info(f"📊 Resumen eliminación: 1 chat, {len(sessions)} sesiones, {total_interactions} interacciones")
    
    return True


async def count_chats_by_project(
    db: AsyncSession,
    project_id: UUID,
    include_archived: bool = False
) -> int:
    """Contar chats de un proyecto."""
    statement = select(Chat).where(
        Chat.project_id == project_id,
        Chat.deleted_at.is_(None)
    )
    
    if not include_archived:
        statement = statement.where(Chat.is_archived == False)
    
    result = await db.exec(statement)
    return len(result.all()) 