from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from .base import BaseModel
from .interaction_step import InteractionStep


class IAResponse(BaseModel, table=True):
    """Modelo de respuesta de IA para un paso de interacción."""
    
    __tablename__ = "ia_responses"

    interaction_step_id: UUID = Field(foreign_key="interaction_steps.id", index=True)
    ia_provider_name: str = Field(index=True)
    raw_response_text: str
    latency_ms: int
    error_message: Optional[str] = Field(default=None)
    received_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    interaction_step: InteractionStep = Relationship(back_populates="ia_responses") 