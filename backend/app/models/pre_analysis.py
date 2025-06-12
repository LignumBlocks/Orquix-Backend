from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class PreAnalysisResult(BaseModel):
    """
    Resultado del análisis previo de un prompt del usuario.
    
    Campos:
    - interpreted_intent: Paráfrasis de lo que entiende el sistema
    - clarification_questions: Lista de preguntas para aclarar ambigüedades
    - refined_prompt_candidate: Versión refinada del prompt (solo si está completo)
    """
    interpreted_intent: str
    clarification_questions: List[str]
    refined_prompt_candidate: Optional[str] = None

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
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ClarificationRequest(BaseModel):
    """Request para continuar una sesión de clarificación."""
    session_id: Optional[UUID] = None  # None para nueva sesión
    project_id: UUID
    user_response: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_response": "Es para Medellín, 4 días, tengo $800 dólares"
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
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "analysis_result": {
                    "interpreted_intent": "El usuario quiere planificar un viaje a Medellín",
                    "clarification_questions": ["¿Qué actividades te interesan más?"],
                    "refined_prompt_candidate": None
                },
                "is_complete": False,
                "next_questions": ["¿Qué actividades te interesan más?"]
            }
        } 