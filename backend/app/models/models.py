from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlmodel import Field, Relationship, SQLModel, Column, Text, DateTime, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    
    email: str = Field(unique=True, index=True)
    name: str
    google_id: str = Field(unique=True, index=True)
    avatar_url: str

    # Relationships
    projects: List["Project"] = Relationship(back_populates="user")
    interaction_events: List["InteractionEvent"] = Relationship(back_populates="user")
    context_chunks: List["ContextChunk"] = Relationship(back_populates="user")


class Project(SQLModel, table=True):
    __tablename__ = "projects"
    __table_args__ = {'extend_existing': True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, index=True)

    user_id: UUID = Field(foreign_key="users.id", index=True)
    name: str
    description: str
    moderator_personality: str = Field(default="Analytical")
    moderator_temperature: float = Field(default=0.7)
    moderator_length_penalty: float = Field(default=0.5)
    archived_at: Optional[datetime] = Field(default=None)

    # Relationships
    user: User = Relationship(back_populates="projects")
    interaction_events: List["InteractionEvent"] = Relationship(back_populates="project")
    context_chunks: List["ContextChunk"] = Relationship(back_populates="project")


class ModeratedSynthesis(SQLModel, table=True):
    __tablename__ = "moderated_syntheses"
    __table_args__ = {'extend_existing': True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, index=True)

    synthesis_text: str = Field(sa_column=Column(Text, nullable=False))


class InteractionEvent(SQLModel, table=True):
    __tablename__ = "interaction_events"
    __table_args__ = {'extend_existing': True}

    id: UUID = Field(
        sa_column=Column(PostgresUUID(as_uuid=True), primary_key=True, nullable=False)
    )

    project_id: UUID = Field(foreign_key="projects.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    user_prompt_text: str = Field(sa_column=Column(Text, nullable=False))
    context_used_summary: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    moderated_synthesis_id: Optional[UUID] = Field(default=None, foreign_key="moderated_syntheses.id")
    user_feedback_score: Optional[int] = Field(default=None, sa_column=Column(Integer, nullable=True))
    user_feedback_comment: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
    deleted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True, index=True))
    ai_responses_json: Optional[str] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    moderator_synthesis_json: Optional[str] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    context_used: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, default=False))
    context_preview: Optional[str] = Field(default=None, sa_column=Column(String(500), nullable=True))
    processing_time_ms: Optional[int] = Field(default=None, sa_column=Column(Integer, nullable=True))
    
    # NUEVO: Tipo de interacción
    interaction_type: str = Field(default="final_query", sa_column=Column(String(50), nullable=False, default="final_query"))
    # Valores posibles: "context_building", "final_query"
    
    # NUEVO: Estado de sesión para construcción de contexto
    session_status: Optional[str] = Field(default=None, sa_column=Column(String(20), nullable=True))
    # Valores posibles: "active", "completed", "abandoned" (solo para context_building)

    # Relationships
    project: Project = Relationship(back_populates="interaction_events")
    user: User = Relationship(back_populates="interaction_events")
    ia_responses: List["IAResponse"] = Relationship(back_populates="interaction_event")
    moderated_synthesis: Optional[ModeratedSynthesis] = Relationship()


class IAResponse(SQLModel, table=True):
    __tablename__ = "ia_responses"
    __table_args__ = {'extend_existing': True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, index=True)

    interaction_event_id: UUID = Field(foreign_key="interaction_events.id", index=True)
    ia_provider_name: str = Field(index=True)
    raw_response_text: str
    latency_ms: int
    error_message: Optional[str] = Field(default=None)
    received_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    interaction_event: InteractionEvent = Relationship(back_populates="ia_responses")


class ContextChunk(SQLModel, table=True):
    __tablename__ = "context_chunks"
    __table_args__ = {'extend_existing': True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, index=True)

    project_id: UUID = Field(foreign_key="projects.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    content_text: str = Field(sa_column=Column(Text, nullable=False))
    content_embedding: List[float] = Field(sa_type=Vector(1536))
    source_type: str = Field(index=True)
    source_identifier: str = Field(index=True)

    # Relationships
    project: Project = Relationship(back_populates="context_chunks")
    user: User = Relationship(back_populates="context_chunks") 