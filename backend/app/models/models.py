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
    chats: List["Chat"] = Relationship(back_populates="user")
    sessions: List["Session"] = Relationship(back_populates="user")


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
    chats: List["Chat"] = Relationship(back_populates="project")


class ModeratedSynthesis(SQLModel, table=True):
    __tablename__ = "moderated_syntheses"
    __table_args__ = {'extend_existing': True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, index=True)

    synthesis_text: str = Field(sa_column=Column(Text, nullable=False))


class InteractionEvent(SQLModel, table=True):
    """Timeline cronológico de eventos en sesiones de chat"""
    __tablename__ = "interaction_events"
    __table_args__ = {'extend_existing': True}

    # ✅ Campos esenciales
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="sessions.id", index=True)  # 🔗 RELACIÓN PRINCIPAL
    
    # ✅ Tipo de evento
    event_type: str = Field(index=True)  # "user_message" | "ai_response" | "context_update" | "session_complete"
    
    # ✅ Contenido del evento
    content: str = Field(sa_column=Column(Text, nullable=False))  # Mensaje del usuario o respuesta de IA
    
    # ✅ Metadatos del evento
    event_data: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))  # Datos adicionales flexibles
    
    # ✅ Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
    deleted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True, index=True))

    # ✅ Campos de compatibilidad (mantener por ahora para migración gradual)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    user_prompt_text: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))  # DEPRECATED: usar content
    
    # Relationships
    project: Project = Relationship(back_populates="interaction_events")
    user: User = Relationship(back_populates="interaction_events")
    session: "Session" = Relationship()  # 🔗 NUEVA RELACIÓN PRINCIPAL


class IAPrompt(SQLModel, table=True):
    __tablename__ = "ia_prompts"
    __table_args__ = {'extend_existing': True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, index=True)

    project_id: UUID = Field(foreign_key="projects.id", index=True)
    context_session_id: Optional[UUID] = Field(default=None, index=True)
    original_query: str = Field(sa_column=Column(Text, nullable=False))
    generated_prompt: str = Field(sa_column=Column(Text, nullable=False))
    is_edited: bool = Field(default=False)
    edited_prompt: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    status: str = Field(default="generated", index=True)
    
    # Relationships
    project: Project = Relationship()
    ia_responses: List["IAResponse"] = Relationship(back_populates="ia_prompt")


class IAResponse(SQLModel, table=True):
    __tablename__ = "ia_responses"
    __table_args__ = {'extend_existing': True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, index=True)

    ia_prompt_id: UUID = Field(foreign_key="ia_prompts.id", index=True)
    ia_provider_name: str = Field(index=True)
    raw_response_text: str
    latency_ms: int
    error_message: Optional[str] = Field(default=None)
    received_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    ia_prompt: IAPrompt = Relationship(back_populates="ia_responses")


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


class Chat(SQLModel, table=True):
    __tablename__ = "chats"
    __table_args__ = {'extend_existing': True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, index=True)

    project_id: UUID = Field(foreign_key="projects.id", index=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", index=True)
    title: str = Field(sa_column=Column(Text, nullable=False))
    is_archived: bool = Field(default=False)

    # Relationships
    project: Project = Relationship()
    user: Optional[User] = Relationship()
    sessions: List["Session"] = Relationship(back_populates="chat")


class Session(SQLModel, table=True):
    __tablename__ = "sessions"
    __table_args__ = {'extend_existing': True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, index=True)

    chat_id: UUID = Field(foreign_key="chats.id", index=True)
    previous_session_id: Optional[UUID] = Field(default=None, foreign_key="sessions.id", index=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", index=True)
    
    accumulated_context: str = Field(default="", sa_column=Column(Text, nullable=False, default=""))
    final_question: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    status: str = Field(default="active", sa_column=Column(String(20), nullable=False, default="active"))
    order_index: int = Field(sa_column=Column(Integer, nullable=False))
    
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = Field(default=None)

    # Relationships
    chat: Chat = Relationship(back_populates="sessions")
    user: Optional[User] = Relationship()
    previous_session: Optional["Session"] = Relationship(
        sa_relationship_kwargs={"remote_side": "Session.id"}
    )
    interaction_events: List["InteractionEvent"] = Relationship(back_populates="session")

