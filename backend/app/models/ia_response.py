from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from .base import BaseModel


class IAResponse(BaseModel, table=True):
    """Modelo de respuesta de IA para un evento de interacción."""
    
    __tablename__ = "ia_responses"

    interaction_event_id: UUID = Field(foreign_key="interaction_events.id", index=True)
    ia_provider_name: str = Field(index=True)
    raw_response_text: str
    latency_ms: int
    error_message: Optional[str] = Field(default=None)
    received_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    interaction_event: "InteractionEvent" = Relationship(back_populates="ia_responses") 