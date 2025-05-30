from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from uuid import UUID
from pydantic import BaseModel, Field

from app.core.database import get_session
from app.services.context_manager import ContextManager, EmbeddingError
from app.schemas.context import ChunkResponse, ChunkWithSimilarity, ContextBlock
from app.crud.context import get_project_chunks, delete_project_chunks
from app.core.config import settings

router = APIRouter(prefix="/context", tags=["context"])

class TextProcessRequest(BaseModel):
    """
    Modelo de solicitud para procesar texto y generar embeddings.
    """
    text: str = Field(
        ...,
        description="Texto a procesar y convertir en embeddings",
        min_length=1
    )
    project_id: UUID = Field(
        ...,
        description="ID del proyecto al que pertenece el texto"
    )
    user_id: UUID = Field(
        ...,
        description="ID del usuario que envía el texto"
    )
    source_type: str = Field(
        ...,
        description="Tipo de fuente del texto (ej: user_input, ia_response, file_upload)",
        min_length=1
    )
    source_identifier: str = Field(
        ...,
        description="Identificador único de la fuente (ej: message_id, file_name)",
        min_length=1
    )

class SearchRequest(BaseModel):
    """
    Modelo de solicitud para búsqueda de contexto relevante.
    """
    query: str = Field(
        ...,
        description="Texto de la consulta para buscar contexto relevante",
        min_length=1
    )
    project_id: UUID = Field(
        ...,
        description="ID del proyecto donde buscar"
    )
    user_id: Optional[UUID] = Field(
        None,
        description="ID del usuario para filtrar resultados (opcional)"
    )
    top_k: Optional[int] = Field(
        5,
        description="Número máximo de resultados a retornar",
        ge=1,
        le=20
    )
    similarity_threshold: Optional[float] = Field(
        0.3,
        description="Umbral mínimo de similitud (0 a 1)",
        ge=0.0,
        le=1.0
    )

class ContextBlockRequest(BaseModel):
    """
    Modelo de solicitud para generar un bloque de contexto.
    """
    query: str = Field(
        ...,
        description="Texto de la consulta para buscar contexto relevante",
        min_length=1
    )
    project_id: UUID = Field(
        ...,
        description="ID del proyecto donde buscar"
    )
    user_id: Optional[UUID] = Field(
        None,
        description="ID del usuario para filtrar resultados (opcional)"
    )
    max_tokens: Optional[int] = Field(
        None,
        description="Límite máximo de tokens (usa el valor por defecto si no se especifica)",
        gt=0
    )
    top_k: Optional[int] = Field(
        5,
        description="Número máximo de chunks a considerar",
        ge=1,
        le=20
    )
    similarity_threshold: Optional[float] = Field(
        0.3,
        description="Umbral mínimo de similitud (0 a 1)",
        ge=0.0,
        le=1.0
    )

@router.post(
    "/process",
    response_model=List[ChunkResponse],
    summary="Procesa texto y genera embeddings",
    description="""
    Procesa un texto dividiéndolo en chunks semánticamente coherentes,
    genera embeddings para cada chunk y los almacena en la base de datos.
    
    El texto se divide en fragmentos manteniendo párrafos y oraciones completas cuando es posible,
    con un solapamiento para mantener el contexto entre chunks.
    
    Los embeddings se generan usando el modelo sentence-transformers configurado
    (por defecto: all-MiniLM-L6-v2).
    """
)
async def process_text(
    request: TextProcessRequest,
    db: Session = Depends(get_session)
) -> List[ChunkResponse]:
    context_manager = ContextManager(db)
    try:
        chunks = await context_manager.process_and_store_text(
            text=request.text,
            project_id=request.project_id,
            user_id=request.user_id,
            source_type=request.source_type,
            source_identifier=request.source_identifier
        )
        return chunks
    except EmbeddingError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar embeddings: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el texto: {str(e)}"
        )

@router.post(
    "/search",
    response_model=List[ChunkWithSimilarity],
    summary="Busca contexto relevante",
    description="""
    Busca chunks de texto relevantes para una consulta dada.
    
    El proceso:
    1. Genera el embedding de la consulta
    2. Busca chunks similares usando similitud coseno
    3. Retorna los chunks más relevantes con sus puntuaciones
    
    Los resultados están ordenados por similitud descendente.
    """
)
async def search_context(
    request: SearchRequest,
    db: Session = Depends(get_session)
) -> List[ChunkWithSimilarity]:
    context_manager = ContextManager(db)
    try:
        relevant_chunks = await context_manager.find_relevant_context(
            query=request.query,
            project_id=request.project_id,
            user_id=request.user_id,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        return relevant_chunks
    except EmbeddingError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar embeddings para la búsqueda: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar contexto relevante: {str(e)}"
        )

@router.get(
    "/project/{project_id}",
    response_model=List[ChunkResponse],
    summary="Obtiene chunks de un proyecto",
    description="Recupera todos los chunks de texto y embeddings asociados a un proyecto."
)
async def get_chunks(
    project_id: UUID,
    source_type: str | None = None,
    db: Session = Depends(get_session)
) -> List[ChunkResponse]:
    chunks = await get_project_chunks(db, project_id, source_type)
    return chunks

@router.delete(
    "/project/{project_id}",
    summary="Elimina chunks de un proyecto",
    description="Elimina todos los chunks asociados a un proyecto, opcionalmente filtrados por tipo de fuente."
)
async def delete_chunks(
    project_id: UUID,
    source_type: str | None = None,
    db: Session = Depends(get_session)
) -> dict:
    deleted_count = await delete_project_chunks(db, project_id, source_type)
    return {
        "deleted_chunks": deleted_count,
        "message": f"Se eliminaron {deleted_count} chunks exitosamente"
    }

@router.post(
    "/generate-block",
    response_model=ContextBlock,
    summary="Genera un bloque de contexto",
    description="""
    Genera un bloque de contexto coherente a partir de chunks relevantes.
    
    El proceso:
    1. Busca chunks relevantes para la consulta
    2. Los combina en un único texto respetando el límite de tokens
    3. Mantiene la coherencia usando separadores entre chunks
    4. Trunca el texto si es necesario, priorizando los chunks más relevantes
    
    El resultado incluye el texto combinado y metadatos sobre el proceso.
    """
)
async def generate_context_block(
    request: ContextBlockRequest,
    db: Session = Depends(get_session)
) -> ContextBlock:
    context_manager = ContextManager(db)
    try:
        context_block = await context_manager.generate_context_block(
            query=request.query,
            project_id=request.project_id,
            user_id=request.user_id,
            max_tokens=request.max_tokens,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        return context_block
    except EmbeddingError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar embeddings para la búsqueda: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar bloque de contexto: {str(e)}"
        ) 