from typing import List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class ChunkCreate(BaseModel):
    project_id: UUID
    user_id: UUID
    content_text: str
    content_embedding: List[float]
    source_type: str
    source_identifier: str

class ChunkResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    content_text: str
    source_type: str
    source_identifier: str
    created_at: datetime
    updated_at: datetime

class ChunkWithSimilarity(BaseModel):
    """
    Modelo que combina un chunk con su puntuación de similitud.
    """
    chunk: ChunkResponse
    similarity_score: float = Field(
        ...,
        description="Puntuación de similitud coseno (0 a 1, donde 1 es más similar)",
        ge=0.0,  # Mayor o igual a 0
        le=1.0   # Menor o igual a 1
    )

class ContextBlock(BaseModel):
    """
    Modelo que representa un bloque de contexto generado.
    """
    context_text: str = Field(
        ...,
        description="Texto combinado de los chunks relevantes"
    )
    total_tokens: int = Field(
        ...,
        description="Número total de tokens en el bloque de contexto",
        ge=0
    )
    chunks_used: int = Field(
        ...,
        description="Número de chunks incluidos en el bloque",
        ge=0
    )
    was_truncated: bool = Field(
        ...,
        description="Indica si el texto fue truncado para cumplir con el límite de tokens"
    ) 