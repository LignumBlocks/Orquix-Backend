from typing import List, Optional
from sqlmodel import Session, select, and_
from uuid import UUID
from sqlalchemy import text
import numpy as np
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import ContextChunk
from app.schemas.context import ChunkCreate
from app.core.config import settings

# Versiones asíncronas (para producción)
async def create_context_chunk(db: Session, chunk: ChunkCreate) -> ContextChunk:
    """
    Crea un nuevo chunk de contexto en la base de datos.
    """
    db_chunk = ContextChunk(
        project_id=chunk.project_id,
        user_id=chunk.user_id,
        content_text=chunk.content_text,
        content_embedding=chunk.content_embedding,
        source_type=chunk.source_type,
        source_identifier=chunk.source_identifier
    )
    db.add(db_chunk)
    await db.commit()
    await db.refresh(db_chunk)
    return db_chunk

# Versiones síncronas (para pruebas)
def create_context_chunk_sync(db: Session, chunk: ChunkCreate) -> ContextChunk:
    """
    Crea un nuevo chunk de contexto en la base de datos (versión síncrona).
    """
    db_chunk = ContextChunk(
        project_id=chunk.project_id,
        user_id=chunk.user_id,
        content_text=chunk.content_text,
        content_embedding=chunk.content_embedding,
        source_type=chunk.source_type,
        source_identifier=chunk.source_identifier
    )
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk

async def get_project_chunks(
    db: Session,
    project_id: UUID,
    source_type: Optional[str] = None
) -> List[ContextChunk]:
    """
    Obtiene todos los chunks de un proyecto, opcionalmente filtrados por tipo de fuente.
    """
    query = select(ContextChunk).where(ContextChunk.project_id == project_id)
    if source_type:
        query = query.where(ContextChunk.source_type == source_type)
    
    result = await db.execute(query)
    return result.scalars().all()

async def find_similar_chunks(
    db: Session,
    query_embedding: List[float],
    project_id: UUID,
    user_id: Optional[UUID] = None,
    top_k: int = 5,
    similarity_threshold: Optional[float] = None
) -> List[ContextChunk]:
    """
    Busca los chunks más similares a un embedding dado usando similitud coseno.
    
    Args:
        db: Sesión de base de datos
        query_embedding: Vector de embedding de la consulta
        project_id: ID del proyecto para filtrar
        user_id: ID del usuario para filtrar (opcional)
        top_k: Número de resultados a retornar
        similarity_threshold: Umbral mínimo de similitud (opcional)
    
    Returns:
        Lista de chunks ordenados por similitud descendente
    """
    # Construimos la consulta base
    query = select(ContextChunk).where(
        ContextChunk.project_id == project_id,
        ContextChunk.deleted_at.is_(None)
    )
    
    # Añadimos filtro por usuario si se especifica
    if user_id:
        query = query.where(ContextChunk.user_id == user_id)
    
    # Añadimos la condición de similitud coseno
    cosine_similarity = text("content_embedding <=> CAST(:embedding AS vector)")
    query = query.order_by(cosine_similarity)
    
    # Añadimos el umbral de similitud si se especifica
    if similarity_threshold is not None:
        # Crear una nueva expresión de texto para la comparación
        threshold_condition = text("content_embedding <=> CAST(:embedding AS vector) <= :threshold")
        query = query.where(threshold_condition)
    
    # Limitamos el número de resultados
    query = query.limit(top_k)
    
    # Preparar parámetros
    params = {"embedding": str(query_embedding)}
    if similarity_threshold is not None:
        params["threshold"] = similarity_threshold
    
    # Ejecutamos la consulta
    result = await db.execute(query, params)
    
    return result.scalars().all()

def find_similar_chunks_sync(
    db: Session,
    query_embedding: List[float],
    project_id: UUID,
    user_id: Optional[UUID] = None,
    top_k: int = 5,
    similarity_threshold: Optional[float] = None
) -> List[ContextChunk]:
    """
    Busca los chunks más similares a un embedding dado usando similitud coseno (versión síncrona).
    """
    # Construimos la consulta base
    query = select(ContextChunk).where(
        ContextChunk.project_id == project_id,
        ContextChunk.deleted_at.is_(None)
    )
    
    # Añadimos filtro por usuario si se especifica
    if user_id:
        query = query.where(ContextChunk.user_id == user_id)
    
    # Añadimos la condición de similitud coseno
    cosine_similarity = text("content_embedding <=> CAST(:embedding AS vector)")
    query = query.order_by(cosine_similarity)
    
    # Añadimos el umbral de similitud si se especifica
    if similarity_threshold is not None:
        # Crear una nueva expresión de texto para la comparación
        threshold_condition = text("content_embedding <=> CAST(:embedding AS vector) <= :threshold")
        query = query.where(threshold_condition)
    
    # Limitamos el número de resultados
    query = query.limit(top_k)
    
    # Preparar parámetros
    params = {"embedding": str(query_embedding)}
    if similarity_threshold is not None:
        params["threshold"] = similarity_threshold
    
    # Ejecutamos la consulta
    result = db.execute(query, params)
    
    return result.scalars().all()

async def delete_project_chunks(
    db: Session,
    project_id: UUID,
    source_type: Optional[str] = None
) -> int:
    """
    Elimina los chunks de un proyecto, opcionalmente filtrados por tipo de fuente.
    Retorna el número de chunks eliminados.
    """
    query = select(ContextChunk).where(ContextChunk.project_id == project_id)
    if source_type:
        query = query.where(ContextChunk.source_type == source_type)
    
    chunks = await db.execute(query)
    chunks = chunks.scalars().all()
    
    for chunk in chunks:
        await db.delete(chunk)
    
    await db.commit()
    return len(chunks) 