from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import json

from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import InteractionEvent, Session
from app.schemas.interaction import InteractionEventCreate, InteractionEventResponse


# ✅ NUEVAS FUNCIONES PARA TIMELINE

async def create_timeline_event(
    db: AsyncSession,
    session_id: UUID,
    event_type: str,
    content: str,
    event_data: Optional[Dict[str, Any]] = None,
    project_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None
) -> InteractionEvent:
    """
    Crear un nuevo evento en el timeline de una sesión.
    """
    
    db_event = InteractionEvent(
        session_id=session_id,
        event_type=event_type,
        content=content,
        event_data=event_data,
        project_id=project_id,  # Compatibilidad
        user_id=user_id,  # Compatibilidad
        user_prompt_text=content if event_type == "user_message" else None  # Compatibilidad
    )
    
    db.add(db_event)
    await db.flush()
    await db.refresh(db_event)
    
    return db_event


async def get_session_timeline(
    db: AsyncSession,
    session_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[InteractionEvent]:
    """
    Obtener el timeline completo de eventos de una sesión.
    """
    query = select(InteractionEvent).where(
        InteractionEvent.session_id == session_id
    ).order_by(InteractionEvent.created_at.asc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def count_session_events(
    db: AsyncSession,
    session_id: UUID
) -> int:
    """
    Contar el número de eventos en una sesión.
    """
    from sqlmodel import func
    
    query = select(func.count(InteractionEvent.id)).where(
        InteractionEvent.session_id == session_id
    )
    result = await db.execute(query)
    return result.scalar() or 0


async def get_events_by_type(
    db: AsyncSession,
    session_id: UUID,
    event_type: str
) -> List[InteractionEvent]:
    """
    Obtener eventos de un tipo específico en una sesión.
    """
    query = select(InteractionEvent).where(
        and_(
            InteractionEvent.session_id == session_id,
            InteractionEvent.event_type == event_type
        )
    ).order_by(InteractionEvent.created_at.asc())
    
    result = await db.execute(query)
    return result.scalars().all()


# ✅ FUNCIONES LEGACY (mantener para compatibilidad)

async def create_interaction(
    db: AsyncSession,
    interaction_data: Dict[str, Any]
) -> InteractionEvent:
    """
    Crear un nuevo evento de interacción en la base de datos - LEGACY.
    """
    
    # Extraer session_id del interaction_data o usar None
    session_id = interaction_data.get("session_id")
    if not session_id:
        # Si no hay session_id, crear un evento legacy
        # Buscar o crear una sesión temporal
        pass
    
    # Crear evento usando la nueva estructura
    return await create_timeline_event(
        db=db,
        session_id=UUID(session_id) if session_id else None,
        event_type="user_message",  # Asumir que es mensaje de usuario
        content=interaction_data.get("user_prompt", ""),
        event_data={
            "ai_responses": interaction_data.get("ai_responses", []),
            "moderator_synthesis": interaction_data.get("moderator_synthesis", {}),
            "processing_time_ms": interaction_data.get("processing_time_ms", 0)
        },
        project_id=UUID(interaction_data["project_id"]) if interaction_data.get("project_id") else None,
        user_id=UUID(interaction_data["user_id"]) if interaction_data.get("user_id") else None
    )


async def get_interaction_by_id(
    db: AsyncSession,
    interaction_id: UUID,
    project_id: UUID,
    user_id: UUID
) -> Optional[InteractionEvent]:
    """
    Obtener una interacción específica por ID - LEGACY.
    """
    query = select(InteractionEvent).where(
        and_(
            InteractionEvent.id == interaction_id,
            InteractionEvent.project_id == project_id,
            InteractionEvent.user_id == user_id
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_project_interactions(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    order_by: str = "created_at",
    order_direction: str = "desc"
) -> List[InteractionEvent]:
    """
    Obtener las interacciones de un proyecto con paginación - LEGACY.
    """
    query = select(InteractionEvent).where(
        and_(
            InteractionEvent.project_id == project_id,
            InteractionEvent.user_id == user_id
        )
    )
    
    # Ordenamiento
    if order_direction.lower() == "desc":
        query = query.order_by(getattr(InteractionEvent, order_by).desc())
    else:
        query = query.order_by(getattr(InteractionEvent, order_by))
    
    # Paginación
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def delete_interaction(
    db: AsyncSession,
    interaction_id: UUID,
    project_id: UUID,
    user_id: UUID
) -> bool:
    """
    Eliminar una interacción específica - LEGACY.
    """
    interaction = await get_interaction_by_id(db, interaction_id, project_id, user_id)
    
    if not interaction:
        return False
    
    await db.delete(interaction)
    return True


async def count_project_interactions(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID
) -> int:
    """
    Contar el número total de interacciones en un proyecto - LEGACY.
    """
    from sqlmodel import func
    
    query = select(func.count(InteractionEvent.id)).where(
        and_(
            InteractionEvent.project_id == project_id,
            InteractionEvent.user_id == user_id
        )
    )
    result = await db.execute(query)
    return result.scalar() or 0


async def get_interaction_stats(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID
) -> Dict[str, Any]:
    """
    Obtener estadísticas básicas de las interacciones de un proyecto - LEGACY.
    """
    from sqlmodel import func
    
    # Consulta para obtener estadísticas
    stats_query = select(
        func.count(InteractionEvent.id).label("total_interactions"),
        func.avg(InteractionEvent.processing_time_ms).label("avg_processing_time"),
        func.min(InteractionEvent.created_at).label("first_interaction"),
        func.max(InteractionEvent.created_at).label("last_interaction")
    ).where(
        and_(
            InteractionEvent.project_id == project_id,
            InteractionEvent.user_id == user_id
        )
    )
    
    result = await db.execute(stats_query)
    stats = result.one()
    
    return {
        "total_interactions": stats.total_interactions or 0,
        "average_processing_time_ms": int(stats.avg_processing_time or 0),
        "first_interaction_date": stats.first_interaction,
        "last_interaction_date": stats.last_interaction
    }


