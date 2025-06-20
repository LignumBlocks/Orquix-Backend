from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel


class IAPromptBase(BaseModel):
    original_query: str
    generated_prompt: str


class IAPromptCreate(IAPromptBase):
    project_id: UUID
    context_session_id: Optional[UUID] = None


class IAPromptUpdate(BaseModel):
    edited_prompt: str


class IAResponseSummary(BaseModel):
    """Resumen de respuesta de IA para incluir en el prompt"""
    id: UUID
    ia_provider_name: str
    created_at: datetime
    latency_ms: int
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class IAPromptResponse(IAPromptBase):
    id: UUID
    project_id: UUID
    context_session_id: Optional[UUID]
    is_edited: bool
    edited_prompt: Optional[str]
    status: str  # generated, edited, executed
    created_at: datetime
    updated_at: datetime
    ia_responses: List[IAResponseSummary] = []

    class Config:
        from_attributes = True


class GeneratePromptRequest(BaseModel):
    """Request para generar un prompt"""
    query: str
    context_session_id: Optional[UUID] = None


class GeneratePromptResponse(BaseModel):
    """Response del endpoint de generar prompt"""
    prompt_id: UUID
    original_query: str
    generated_prompt: str
    project_id: UUID
    context_session_id: Optional[UUID]
    status: str
    created_at: datetime


class ExecutePromptRequest(BaseModel):
    """Request para ejecutar un prompt"""
    prompt_id: UUID
    use_edited_version: bool = False 