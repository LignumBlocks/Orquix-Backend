from uuid import UUID
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlmodel import Field, Relationship, Column, Text, DateTime

from .base import BaseModel
from .project import Project
from .user import User
from app.core.config import settings


class ContextChunk(BaseModel, table=True):
    """Modelo de fragmento de contexto con embedding vectorial."""
    
    __tablename__ = "context_chunks"

    project_id: UUID = Field(foreign_key="projects.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    content_text: str = Field(sa_column=Column(Text, nullable=False))
    content_embedding: list[float] = Field(sa_type=Vector(settings.EMBEDDING_DIMENSION))
    source_type: str = Field(index=True)
    source_identifier: str = Field(index=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        default_factory=datetime.utcnow
    )

    # Relationships según esquema MVP
    project: Project = Relationship(back_populates="context_chunks")
    user: User = Relationship(back_populates="context_chunks") 