from typing import List, Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from .base import BaseModel
from .research_session import ResearchSession
from .moderated_synthesis import ModeratedSynthesis


class InteractionStep(BaseModel, table=True):
    """Modelo de paso de interacción en una sesión de investigación."""
    
    __tablename__ = "interaction_steps"

    session_id: UUID = Field(foreign_key="research_sessions.id", index=True)
    step_order: int = Field(index=True)
    user_prompt_text: str
    context_used_summary: str
    moderator_synthesis_id: Optional[UUID] = Field(
        default=None, foreign_key="moderated_syntheses.id", nullable=True
    )
    user_feedback_score: Optional[int] = Field(default=None)
    user_feedback_comment: Optional[str] = Field(default=None)

    # Relationships
    session: ResearchSession = Relationship(back_populates="interaction_steps")
    ia_responses: List["IAResponse"] = Relationship(back_populates="interaction_step")
    moderated_synthesis: Optional[ModeratedSynthesis] = Relationship() 