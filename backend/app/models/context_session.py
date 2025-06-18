from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class ContextMessage(BaseModel):
    """Un mensaje en la conversación de construcción de contexto."""
    role: str  # "user" o "assistant"
    content: str
    timestamp: datetime
    message_type: Optional[str] = None  # "question", "information", "ready"

class ContextChatRequest(BaseModel):
    """Request para chat de construcción de contexto."""
    user_message: str
    session_id: Optional[UUID] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_message": "Necesito ayuda con mi startup de delivery",
                "session_id": None
            }
        }

class ContextChatResponse(BaseModel):
    """Response del chat de construcción de contexto."""
    session_id: UUID
    ai_response: str
    message_type: str  # "question", "information", "ready"
    accumulated_context: str
    suggestions: List[str] = []
    context_elements_count: int = 0
    suggested_final_question: Optional[str] = None  # Pregunta sugerida cuando message_type es "ready"
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "ai_response": "Entiendo que tienes una startup de delivery. ¿Podrías contarme en qué etapa se encuentra?",
                "message_type": "question",
                "accumulated_context": "Startup de delivery de comida",
                "suggestions": ["Etapa de desarrollo", "Problemas actuales", "Métricas clave"],
                "context_elements_count": 1,
                "suggested_final_question": None
            }
        }

class ContextFinalizeRequest(BaseModel):
    """Request para finalizar contexto y enviar a IAs principales."""
    session_id: UUID
    final_question: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "final_question": "¿Cómo puedo mejorar las conversiones de mi app de delivery?"
            }
        }

class ContextSessionSummary(BaseModel):
    """Resumen de una sesión de contexto."""
    id: UUID
    project_id: UUID
    accumulated_context: str
    messages_count: int
    is_active: bool
    created_at: datetime
    last_activity: datetime

class ContextSession(BaseModel):
    """Sesión de construcción de contexto usando InteractionEvent."""
    id: UUID
    project_id: UUID
    user_id: UUID
    conversation_history: List[ContextMessage]
    accumulated_context: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 