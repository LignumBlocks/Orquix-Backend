from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from .base import BaseModel
from .project import Project
from .user import User
from .moderated_synthesis import ModeratedSynthesis


class ResearchSession(BaseModel, table=True):
    """Modelo de sesión de investigación."""
    
    __tablename__ = "research_sessions"

    project_id: UUID = Field(foreign_key="projects.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    session_start_time: datetime = Field(default_factory=datetime.utcnow)
    initial_user_prompt: str
    moderated_synthesis_id: Optional[UUID] = Field(
        default=None, foreign_key="moderated_syntheses.id", nullable=True
    )

    # Relationships
    project: Project = Relationship(back_populates="research_sessions")
    user: User = Relationship(back_populates="research_sessions")
    interaction_steps: List["InteractionStep"] = Relationship(back_populates="session")
    moderated_synthesis: Optional[ModeratedSynthesis] = Relationship() 