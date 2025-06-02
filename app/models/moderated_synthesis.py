from datetime import datetime
from sqlmodel import Field, Column, Text, DateTime

from .base import BaseModel


class ModeratedSynthesis(BaseModel, table=True):
    """Modelo de síntesis moderada de respuestas IA."""
    
    __tablename__ = "moderated_syntheses"

    synthesis_text: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=datetime.utcnow
    ) 