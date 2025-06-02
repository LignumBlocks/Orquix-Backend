from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import json

from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.interaction import InteractionEvent
from app.schemas.interaction import InteractionEventCreate


async def create_interaction(
    db: AsyncSession,
    interaction_data: Dict[str, Any]
) -> InteractionEvent:
    """
    Crear un nuevo evento de interacción en la base de datos.
    """
    
    # Convertir datos del dict a modelo de creación
    interaction_create = InteractionEventCreate(
        id=UUID(interaction_data["id"]),
        project_id=UUID(interaction_data["project_id"]),
        user_id=UUID(interaction_data["user_id"]),
        user_prompt=interaction_data["user_prompt"],
        ai_responses=interaction_data["ai_responses"],
        moderator_synthesis=interaction_data["moderator_synthesis"],
        context_used=interaction_data["context_used"],
        context_preview=interaction_data.get("context_preview"),
        processing_time_ms=interaction_data["processing_time_ms"],
        created_at=datetime.fromisoformat(interaction_data["created_at"])
    )
    
    # Crear instancia del modelo de base de datos
    db_interaction = InteractionEvent(
        id=interaction_create.id,
        project_id=interaction_create.project_id,
        user_id=interaction_create.user_id,
        user_prompt=interaction_create.user_prompt,
        ai_responses_json=json.dumps(interaction_create.ai_responses),
        moderator_synthesis_json=json.dumps(interaction_create.moderator_synthesis),
        context_used=interaction_create.context_used,
        context_preview=interaction_create.context_preview,
        processing_time_ms=interaction_create.processing_time_ms,
        created_at=interaction_create.created_at
    )
    
    db.add(db_interaction)
    await db.flush()
    await db.refresh(db_interaction)
    
    return db_interaction


async def get_interaction_by_id(
    db: AsyncSession,
    interaction_id: UUID,
    project_id: UUID,
    user_id: UUID
) -> Optional[InteractionEvent]:
    """
    Obtener una interacción específica por ID.
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
    Obtener las interacciones de un proyecto con paginación.
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
    Eliminar una interacción específica.
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
    Contar el número total de interacciones en un proyecto.
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
    Obtener estadísticas básicas de las interacciones de un proyecto.
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