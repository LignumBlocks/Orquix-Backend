from typing import List, Optional
from uuid import UUID
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.schemas.feedback import (
    FeedbackCreate, 
    FeedbackResponse, 
    FeedbackStats,
    FeedbackListResponse
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


@router.post("/", response_model=FeedbackResponse)
async def create_feedback(
    *,
    db: AsyncSession = Depends(get_db),
    feedback_in: FeedbackCreate,
    current_user: SessionUser = Depends(require_auth),
) -> FeedbackResponse:
    """
    POST /api/v1/feedback
    
    Crear nuevo feedback del usuario.
    Recibe ID de referencia, score y comentario opcional.
    """
    user_id = UUID(current_user.id)
    
    # Validaciones adicionales
    if feedback_in.score < 1 or feedback_in.score > 5:
        raise HTTPException(
            status_code=400,
            detail="La puntuación debe estar entre 1 y 5"
        )
    
    # TODO: Implementar validación de que reference_id existe según reference_type
    # Por ejemplo, si reference_type="interaction", verificar que existe la interacción
    
    # TODO: Implementar CRUD para feedback una vez que tengamos los modelos de BD
    # Por ahora simulamos la creación
    
    feedback_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")  # Mock ID
    
    feedback_response = FeedbackResponse(
        id=feedback_id,
        reference_id=feedback_in.reference_id,
        reference_type=feedback_in.reference_type,
        score=feedback_in.score,
        comment=feedback_in.comment,
        category=feedback_in.category,
        created_at=datetime.utcnow()
    )
    
    logger.info(f"Feedback creado: {feedback_id} por usuario {user_id} - Score: {feedback_in.score}")
    
    return feedback_response


@router.get("/", response_model=FeedbackListResponse)
async def list_feedback(
    *,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Número de página"),
    per_page: int = Query(default=20, ge=1, le=100, description="Elementos por página"),
    reference_type: Optional[str] = Query(default=None, description="Filtrar por tipo de referencia"),
    min_score: Optional[int] = Query(default=None, ge=1, le=5, description="Puntuación mínima"),
    max_score: Optional[int] = Query(default=None, ge=1, le=5, description="Puntuación máxima"),
    current_user: SessionUser = Depends(require_auth),
) -> FeedbackListResponse:
    """
    GET /api/v1/feedback
    
    Listar feedback con filtros y paginación.
    Solo administradores pueden ver todo el feedback, usuarios normales solo el suyo.
    """
    user_id = UUID(current_user.id)
    
    # TODO: Implementar consulta real a la BD con filtros
    # Por ahora retornamos datos mock
    
    mock_feedbacks = [
        FeedbackResponse(
            id=UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            reference_id=UUID("11111111-1111-1111-1111-111111111111"),
            reference_type="interaction",
            score=5,
            comment="Excelente síntesis, muy útil",
            category="helpful",
            created_at=datetime.utcnow() - timedelta(hours=2)
        ),
        FeedbackResponse(
            id=UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff"),
            reference_id=UUID("22222222-2222-2222-2222-222222222222"),
            reference_type="synthesis",
            score=4,
            comment="Buena calidad pero podría ser más conciso",
            category="accurate",
            created_at=datetime.utcnow() - timedelta(hours=5)
        )
    ]
    
    # Aplicar filtros mock
    filtered_feedbacks = mock_feedbacks
    if reference_type:
        filtered_feedbacks = [f for f in filtered_feedbacks if f.reference_type == reference_type]
    if min_score:
        filtered_feedbacks = [f for f in filtered_feedbacks if f.score >= min_score]
    if max_score:
        filtered_feedbacks = [f for f in filtered_feedbacks if f.score <= max_score]
    
    # Aplicar paginación
    offset = (page - 1) * per_page
    paginated_feedbacks = filtered_feedbacks[offset:offset + per_page]
    
    total_count = len(filtered_feedbacks)
    has_next = offset + per_page < total_count
    has_prev = page > 1
    
    logger.info(f"Listando feedback - página {page}, total: {total_count}")
    
    return FeedbackListResponse(
        feedbacks=paginated_feedbacks,
        total_count=total_count,
        page=page,
        per_page=per_page,
        has_next=has_next,
        has_prev=has_prev
    )


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    *,
    db: AsyncSession = Depends(get_db),
    reference_type: Optional[str] = Query(default=None, description="Filtrar por tipo de referencia"),
    days: int = Query(default=30, ge=1, le=365, description="Últimos N días"),
    current_user: SessionUser = Depends(require_auth),
) -> FeedbackStats:
    """
    GET /api/v1/feedback/stats
    
    Obtener estadísticas de feedback para análisis.
    """
    user_id = UUID(current_user.id)
    
    # TODO: Implementar consulta real de estadísticas
    # Por ahora retornamos datos mock
    
    mock_stats = FeedbackStats(
        total_feedbacks=157,
        average_score=4.2,
        score_distribution={
            1: 8,
            2: 15,
            3: 23,
            4: 45,
            5: 66
        },
        recent_feedbacks=[
            FeedbackResponse(
                id=UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
                reference_id=UUID("11111111-1111-1111-1111-111111111111"),
                reference_type="interaction",
                score=5,
                comment="Excelente síntesis",
                category="helpful",
                created_at=datetime.utcnow() - timedelta(hours=1)
            ),
            FeedbackResponse(
                id=UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff"),
                reference_id=UUID("22222222-2222-2222-2222-222222222222"),
                reference_type="synthesis",
                score=4,
                comment="Muy bueno",
                category="accurate",
                created_at=datetime.utcnow() - timedelta(hours=3)
            )
        ]
    )
    
    logger.info(f"Obteniendo estadísticas de feedback para {days} días")
    
    return mock_stats


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    *,
    db: AsyncSession = Depends(get_db),
    feedback_id: UUID,
    current_user: SessionUser = Depends(require_auth),
) -> FeedbackResponse:
    """
    GET /api/v1/feedback/{feedback_id}
    
    Obtener feedback específico por ID.
    """
    user_id = UUID(current_user.id)
    
    # TODO: Implementar búsqueda real en BD
    if str(feedback_id) != "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee":
        raise HTTPException(status_code=404, detail="Feedback no encontrado")
    
    mock_feedback = FeedbackResponse(
        id=feedback_id,
        reference_id=UUID("11111111-1111-1111-1111-111111111111"),
        reference_type="interaction",
        score=5,
        comment="Excelente síntesis, muy útil para mi investigación",
        category="helpful",
        created_at=datetime.utcnow() - timedelta(hours=2)
    )
    
    logger.info(f"Obteniendo feedback {feedback_id}")
    
    return mock_feedback


@router.delete("/{feedback_id}")
async def delete_feedback(
    *,
    db: AsyncSession = Depends(get_db),
    feedback_id: UUID,
    current_user: SessionUser = Depends(require_auth),
) -> dict:
    """
    DELETE /api/v1/feedback/{feedback_id}
    
    Eliminar feedback (solo el autor o administradores).
    """
    user_id = UUID(current_user.id)
    
    # TODO: Implementar eliminación real y verificar permisos
    
    logger.info(f"Eliminando feedback {feedback_id} por usuario {user_id}")
    
    return {"message": "Feedback eliminado exitosamente"} 