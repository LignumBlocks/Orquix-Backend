from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlmodel import Field, Relationship

from .base import BaseModel
from .project import Project
from .user import User


class ContextChunk(BaseModel, table=True):
    """Modelo de fragmento de contexto con embedding vectorial."""
    
    __tablename__ = "context_chunks"

    project_id: UUID = Field(foreign_key="projects.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    content_text: str
    content_embedding: list[float] = Field(sa_type=Vector(1536))
    source_type: str = Field(index=True)
    source_identifier: str = Field(index=True)

    # Relationships
    project: Project = Relationship(back_populates="context_chunks")
    user: User = Relationship(back_populates="context_chunks") 