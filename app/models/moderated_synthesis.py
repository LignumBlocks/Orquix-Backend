from sqlmodel import Field

from .base import BaseModel


class ModeratedSynthesis(BaseModel, table=True):
    """Modelo de síntesis moderada de respuestas IA."""
    
    __tablename__ = "moderated_syntheses"

    synthesis_text: str = Field(index=False) 