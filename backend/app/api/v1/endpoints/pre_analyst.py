from fastapi import APIRouter, HTTPException
from app.models.pre_analysis import (
    PreAnalysisRequest, 
    PreAnalysisResult,
    ClarificationRequest,
    ClarificationResponse
)
from app.services.pre_analyst import pre_analyst_service
from app.services.clarification_manager import clarification_manager
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.auth import SessionUser
from fastapi import Depends
from uuid import UUID

router = APIRouter()

def require_auth(current_user: SessionUser = Depends(get_current_user)) -> SessionUser:
    """Helper para requerir autenticación (mock para desarrollo)"""
    return SessionUser(
        id="550e8400-e29b-41d4-a716-446655440000",
        name="Test User", 
        email="test@orquix.com",
        image=None
    )

@router.post("/analyze-prompt", response_model=PreAnalysisResult)
async def analyze_user_prompt(request: PreAnalysisRequest) -> PreAnalysisResult:
    """
    Analiza un prompt del usuario para interpretar su intención y generar
    preguntas de clarificación si es necesario.
    
    Este endpoint es útil para testing y puede ser usado por el frontend
    para implementar un flujo de clarificación iterativo.
    
    Args:
        request: Contiene el user_prompt_text a analizar
        
    Returns:
        PreAnalysisResult con la interpretación y preguntas de clarificación
        
    Raises:
        HTTPException: Si hay error en el análisis o prompt vacío
    """
    if not request.user_prompt_text.strip():
        raise HTTPException(
            status_code=400, 
            detail="user_prompt_text no puede estar vacío"
        )
    
    try:
        result = await pre_analyst_service.analyze_prompt(request.user_prompt_text)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analizando el prompt: {str(e)}"
        )

@router.post("/clarification", response_model=ClarificationResponse)
async def start_or_continue_clarification(
    request: ClarificationRequest,
    current_user: SessionUser = Depends(require_auth)
) -> ClarificationResponse:
    """
    Inicia una nueva sesión de clarificación o continúa una existente.
    
    Este endpoint maneja el flujo iterativo de clarificación cuando el PreAnalyst
    detecta que necesita más información del usuario.
    
    Args:
        request: ClarificationRequest con session_id (opcional), project_id y user_response
        current_user: Usuario autenticado
        
    Returns:
        ClarificationResponse con el estado de la sesión y próximos pasos
        
    Raises:
        HTTPException: Si hay errores en la sesión o análisis
    """
    if not request.user_response.strip():
        raise HTTPException(
            status_code=400,
            detail="user_response no puede estar vacío"
        )
    
    try:
        user_id = UUID(current_user.id)
        
        if request.session_id is None:
            # Iniciar nueva sesión de clarificación
            response = await clarification_manager.start_clarification_session(
                project_id=request.project_id,
                user_id=user_id,
                initial_prompt=request.user_response
            )
        else:
            # Verificar si se debe forzar el avance
            if request.force_proceed:
                response = clarification_manager.force_proceed_session(request.session_id)
                if not response:
                    raise HTTPException(
                        status_code=404,
                        detail="Sesión de clarificación no encontrada"
                    )
            else:
                # Continuar sesión normalmente
                response = await clarification_manager.continue_clarification_session(
                    session_id=request.session_id,
                    user_response=request.user_response
                )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en sesión de clarificación: {str(e)}"
        )

@router.get("/clarification/{session_id}", response_model=ClarificationResponse)
async def get_clarification_session(
    session_id: UUID,
    current_user: SessionUser = Depends(require_auth)
) -> ClarificationResponse:
    """
    Obtiene el estado actual de una sesión de clarificación.
    
    Args:
        session_id: ID de la sesión de clarificación
        current_user: Usuario autenticado
        
    Returns:
        ClarificationResponse con el estado actual de la sesión
        
    Raises:
        HTTPException: Si la sesión no existe
    """
    try:
        session = clarification_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Sesión de clarificación no encontrada"
            )
        
        # Verificar que la sesión pertenece al usuario
        user_id = UUID(current_user.id)
        if session.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para acceder a esta sesión"
            )
        
        return ClarificationResponse(
            session_id=session.session_id,
            analysis_result=session.current_analysis,
            conversation_history=session.conversation_history,
            is_complete=session.is_complete,
            final_refined_prompt=session.final_refined_prompt,
            next_questions=session.current_analysis.clarification_questions if session.current_analysis else []
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo sesión: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check para el servicio PreAnalyst."""
    return {"status": "ok", "service": "PreAnalyst"} 