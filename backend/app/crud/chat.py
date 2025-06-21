from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import Chat


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
    """Eliminar un chat (soft delete)."""
    chat = await get_chat(db, chat_id)
    if not chat:
        return False
    
    chat.deleted_at = datetime.utcnow()
    await db.commit()
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