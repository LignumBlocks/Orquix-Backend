from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from .base import BaseModel
from .user import User


class Project(BaseModel, table=True):
    """Modelo de proyecto de investigación."""
    
    __tablename__ = "projects"

    user_id: UUID = Field(foreign_key="users.id", index=True)
    name: str
    description: str
    moderator_personality: str = Field(default="Analytical")
    moderator_temperature: float = Field(default=0.7)
    moderator_length_penalty: float = Field(default=0.5)
    archived_at: Optional[datetime] = Field(default=None)

    # Relationships
    user: User = Relationship(back_populates="projects")
    research_sessions: List["ResearchSession"] = Relationship(back_populates="project")
    context_chunks: List["ContextChunk"] = Relationship(back_populates="project") 