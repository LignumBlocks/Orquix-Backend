from datetime import datetime
from typing import Optional
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel


class User(BaseModel, table=True):
    __tablename__ = "users"

    email: str = Field(unique=True, index=True)
    name: str
    avatar_url: Optional[str] = None

    # Relationships
    projects: list["Project"] = Relationship(back_populates="user")
    research_sessions: list["ResearchSession"] = Relationship(back_populates="user")
    context_chunks: list["ContextChunk"] = Relationship(back_populates="user")


class Project(BaseModel, table=True):
    __tablename__ = "projects"

    user_id: UUID = Field(foreign_key="users.id", index=True)
    name: str
    description: str
    moderator_personality: str
    archived_at: Optional[datetime] = Field(default=None)

    # Relationships
    user: User = Relationship(back_populates="projects")
    research_sessions: list["ResearchSession"] = Relationship(back_populates="project")
    context_chunks: list["ContextChunk"] = Relationship(back_populates="project")


class ResearchSession(BaseModel, table=True):
    __tablename__ = "research_sessions"

    project_id: UUID = Field(foreign_key="projects.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    session_start_time: datetime = Field(default_factory=datetime.utcnow)
    initial_user_prompt: str
    moderated_synthesis_id: Optional[UUID] = Field(foreign_key="moderated_syntheses.id", nullable=True)

    # Relationships
    project: Project = Relationship(back_populates="research_sessions")
    user: User = Relationship(back_populates="research_sessions")
    interaction_steps: list["InteractionStep"] = Relationship(back_populates="session")
    moderated_synthesis: Optional["ModeratedSynthesis"] = Relationship()


class InteractionStep(BaseModel, table=True):
    __tablename__ = "interaction_steps"

    session_id: UUID = Field(foreign_key="research_sessions.id", index=True)
    step_order: int = Field(index=True)
    user_prompt_text: str
    context_used_summary: str
    moderator_synthesis_id: Optional[UUID] = Field(foreign_key="moderated_syntheses.id", nullable=True)
    user_feedback_score: Optional[int] = None

    # Relationships
    session: ResearchSession = Relationship(back_populates="interaction_steps")
    ia_responses: list["IAResponse"] = Relationship(back_populates="interaction_step")
    moderated_synthesis: Optional["ModeratedSynthesis"] = Relationship()


class IAResponse(BaseModel, table=True):
    __tablename__ = "ia_responses"

    interaction_step_id: UUID = Field(foreign_key="interaction_steps.id", index=True)
    ia_provider_name: str = Field(index=True)
    raw_response_text: str
    latency_ms: int
    error_message: Optional[str] = None

    # Relationships
    interaction_step: InteractionStep = Relationship(back_populates="ia_responses")


class ModeratedSynthesis(BaseModel, table=True):
    __tablename__ = "moderated_syntheses"

    synthesis_text: str


class ContextChunk(BaseModel, table=True):
    __tablename__ = "context_chunks"

    project_id: UUID = Field(foreign_key="projects.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    content_text: str
    content_embedding: list[float] = Field(sa_type=Vector(1536))
    source_type: str
    source_identifier: str

    # Relationships
    project: Project = Relationship(back_populates="context_chunks")
    user: User = Relationship(back_populates="context_chunks") 