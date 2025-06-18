from typing import List, Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.crud import interaction as interaction_crud
from app.schemas.interaction import (
    InteractionHistoryResponse, 
    InteractionDetailResponse, 
    InteractionSummary,
    InteractionEvent
)
from app.schemas.auth import SessionUser
from app.api.v1.endpoints.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def require_auth(current_user: Optional[SessionUser] = Depends(get_current_user)) -> SessionUser:
    """Helper para requerir autenticación"""
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Autenticación requerida"
        )
    return current_user


@router.get("/{project_id}/interaction_events", response_model=InteractionHistoryResponse)
async def get_interaction_history(
    project_id: UUID,
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
    order_by: str = Query("created_at", description="Campo para ordenar"),
    order_direction: str = Query("desc", regex="^(asc|desc)$", description="Dirección del ordenamiento"),
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth),
) -> InteractionHistoryResponse:
    """
    GET /api/v1/projects/{project_id}/interaction_events
    
    Obtener historial paginado de interacciones del proyecto.
    """
    user_id = UUID(current_user.id)
    
    try:
        # Calcular skip para paginación
        skip = (page - 1) * per_page
        
        # Obtener interacciones
        interactions = await interaction_crud.get_project_interactions(
            db=db,
            project_id=project_id,
            user_id=user_id,
            skip=skip,
            limit=per_page,
            order_by=order_by,
            order_direction=order_direction
        )
        
        # Obtener conteo total
        total_count = await interaction_crud.count_project_interactions(
            db=db,
            project_id=project_id,
            user_id=user_id
        )
        
        # Convertir a summaries
        interaction_summaries = []
        for interaction in interactions:
            # Parsear síntesis para obtener preview
            synthesis_preview = "Sin síntesis disponible"
            if interaction.moderator_synthesis_json:
                import json
                synthesis_data = json.loads(interaction.moderator_synthesis_json)
                synthesis_text = synthesis_data.get("synthesis_text", "")
                synthesis_preview = synthesis_text[:300] + "..." if len(synthesis_text) > 300 else synthesis_text
            
            summary = InteractionSummary(
                id=interaction.id,
                user_prompt=interaction.user_prompt_text[:200] + "..." if len(interaction.user_prompt_text) > 200 else interaction.user_prompt_text,
                synthesis_preview=synthesis_preview,
                moderator_quality=synthesis_data.get("quality", "unknown") if interaction.moderator_synthesis_json else "unknown",
                created_at=interaction.created_at,
                processing_time_ms=interaction.processing_time_ms or 0
            )
            interaction_summaries.append(summary)
        
        # Calcular metadatos de paginación
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        logger.info(f"Historial obtenido: {len(interactions)} interacciones, página {page}")
        
        return InteractionHistoryResponse(
            interactions=interaction_summaries,
            total_count=total_count,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo historial de proyecto {project_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo historial: {str(e)}"
        )


@router.get("/{project_id}/interaction_events/{interaction_id}", response_model=InteractionDetailResponse)
async def get_interaction_detail(
    project_id: UUID,
    interaction_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth),
) -> InteractionDetailResponse:
    """
    GET /api/v1/projects/{project_id}/interaction_events/{interaction_id}
    
    Obtener detalles completos de una interacción específica.
    """
    user_id = UUID(current_user.id)
    
    try:
        # Obtener interacción
        interaction = await interaction_crud.get_interaction_by_id(
            db=db,
            interaction_id=interaction_id,
            project_id=project_id,
            user_id=user_id
        )
        
        if not interaction:
            raise HTTPException(
                status_code=404,
                detail="Interacción no encontrada"
            )
        
        # Convertir a formato de respuesta
        import json
        
        # Parsear respuestas de IA
        ai_responses = []
        if interaction.ai_responses_json:
            ai_responses_data = json.loads(interaction.ai_responses_json)
            # Aquí podrías convertir a StandardAIResponse si es necesario
            ai_responses = ai_responses_data
        
        # Parsear síntesis del moderador
        moderator_synthesis = None
        if interaction.moderator_synthesis_json:
            moderator_synthesis = json.loads(interaction.moderator_synthesis_json)
        
        # Crear evento de interacción
        interaction_event = InteractionEvent(
            id=interaction.id,
            project_id=interaction.project_id,
            user_prompt=interaction.user_prompt_text,
            ai_responses=ai_responses,  # Como dict por ahora
            moderator_synthesis=moderator_synthesis,
            created_at=interaction.created_at,
            processing_time_ms=interaction.processing_time_ms or 0  # Manejar valores None
        )
        
        logger.info(f"Detalles obtenidos para interacción {interaction_id}")
        
        return InteractionDetailResponse(
            interaction=interaction_event,
            synthesis_details=None  # TODO: Implementar si se necesita
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo detalles de interacción {interaction_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo detalles: {str(e)}"
        )


@router.delete("/{project_id}/interaction_events/{interaction_id}")
async def delete_interaction(
    project_id: UUID,
    interaction_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth),
) -> dict:
    """
    DELETE /api/v1/projects/{project_id}/interaction_events/{interaction_id}
    
    Eliminar una interacción específica.
    """
    user_id = UUID(current_user.id)
    
    try:
        # Intentar eliminar la interacción
        deleted = await interaction_crud.delete_interaction(
            db=db,
            interaction_id=interaction_id,
            project_id=project_id,
            user_id=user_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Interacción no encontrada"
            )
        
        await db.commit()
        
        logger.info(f"Interacción {interaction_id} eliminada exitosamente")
        
        return {
            "message": "Interacción eliminada exitosamente",
            "interaction_id": str(interaction_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando interacción {interaction_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando interacción: {str(e)}"
        ) 