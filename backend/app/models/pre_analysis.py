from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class PreAnalysisResult(BaseModel):
    """
    Resultado del análisis previo de un prompt del usuario.
    
    Campos:
    - interpreted_intent: Paráfrasis de lo que entiende el sistema
    - clarification_questions: Lista de preguntas para aclarar ambigüedades
    - refined_prompt_candidate: Versión refinada del prompt (SIEMPRE presente)
    """
    interpreted_intent: str
    clarification_questions: List[str]
    refined_prompt_candidate: str  # Ahora SIEMPRE presente, no Optional

class PreAnalysisRequest(BaseModel):
    """Request para el análisis de un prompt del usuario."""
    user_prompt_text: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_prompt_text": "necesito ayuda con el presupuesto de mi viaje"
            }
        }

class ConversationTurn(BaseModel):
    """Un turno en la conversación de clarificación."""
    role: str  # "user" o "assistant"
    content: str
    timestamp: Optional[str] = None

class ClarificationSession(BaseModel):
    """Sesión de clarificación iterativa con el PreAnalyst."""
    session_id: UUID
    project_id: UUID
    user_id: UUID
    conversation_history: List[ConversationTurn]
    current_analysis: Optional[PreAnalysisResult] = None
    is_complete: bool = False
    final_refined_prompt: Optional[str] = None
    force_proceed: bool = False  # Nuevo campo para opt-in
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ClarificationRequest(BaseModel):
    """Request para continuar una sesión de clarificación."""
    session_id: Optional[UUID] = None  # None para nueva sesión
    project_id: UUID
    user_response: str
    force_proceed: bool = False  # Nuevo campo para saltar clarificaciones
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_response": "Es para Medellín, 4 días, tengo $800 dólares",
                "force_proceed": False
            }
        }

class ClarificationResponse(BaseModel):
    """Response de una sesión de clarificación."""
    session_id: UUID
    analysis_result: PreAnalysisResult
    conversation_history: List[ConversationTurn]
    is_complete: bool
    final_refined_prompt: Optional[str] = None
    next_questions: List[str] = []
    can_force_proceed: bool = True  # Nuevo campo para indicar si se puede forzar
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "analysis_result": {
                    "interpreted_intent": "El usuario quiere planificar un viaje a Medellín",
                    "clarification_questions": ["¿Qué actividades te interesan más?"],
                    "refined_prompt_candidate": "Planifica un viaje de 4 días a Medellín con presupuesto de $800 dólares"
                },
                "is_complete": False,
                "next_questions": ["¿Qué actividades te interesan más?"],
                "can_force_proceed": True
            }
        } 