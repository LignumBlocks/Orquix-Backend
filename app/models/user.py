from typing import List, Optional
from sqlmodel import Field, Relationship

from .base import BaseModel


class User(BaseModel, table=True):
    """Modelo de usuario."""
    
    __tablename__ = "users"

    email: str = Field(unique=True, index=True)
    name: str
    google_id: str = Field(unique=True, index=True)
    avatar_url: str

    # Relationships
    projects: List["Project"] = Relationship(back_populates="user")
    research_sessions: List["ResearchSession"] = Relationship(back_populates="user")
    context_chunks: List["ContextChunk"] = Relationship(back_populates="user") 