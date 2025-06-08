from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
import asyncio
import logging
from datetime import datetime
import numpy as np
import tiktoken

from openai import AsyncOpenAI
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import ContextChunk
from app.schemas.context import ChunkCreate, ChunkWithSimilarity, ContextBlock
from app.crud.context import create_context_chunk, find_similar_chunks
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingError(Exception):
    """Error durante la generación de embeddings."""
    pass

class TokenLimitError(Exception):
    """Error cuando se excede el límite de tokens."""
    pass

class ContextManager:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Inicializamos el cliente de OpenAI
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = "text-embedding-3-small"
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY
        # Inicializamos el tokenizer de tiktoken
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # Compatible con la mayoría de modelos

    def create_chunks(self, text: str) -> List[str]:
        """
        Divide el texto en chunks con solapamiento.
        Estrategia MVP: división por tamaño fijo con solapamiento.
        """
        # Dividimos primero por párrafos para mantener coherencia semántica
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Si el párrafo por sí solo excede el tamaño máximo, lo dividimos
            if len(paragraph) > self.chunk_size:
                sub_chunks = self._split_large_paragraph(paragraph)
                chunks.extend(sub_chunks)
                continue
                
            # Si añadir el párrafo excede el tamaño máximo, guardamos el chunk actual
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk = current_chunk + " " + paragraph if current_chunk else paragraph
        
        # Añadimos el último chunk si existe
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """
        Divide un párrafo grande en chunks más pequeños, intentando mantener
        oraciones completas cuando sea posible.
        """
        chunks = []
        current_chunk = ""
        sentences = paragraph.split('. ')
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = current_chunk + ". " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Genera el embedding para un texto dado usando la API de OpenAI.
        Incluye manejo de errores y reintentos.
        """
        for attempt in range(self.max_retries):
            try:
                response = await self.client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Error al generar embedding (intento {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise EmbeddingError(f"Error al generar embedding después de {self.max_retries} intentos: {str(e)}")

    async def process_and_store_text(
        self,
        text: str,
        project_id: UUID,
        user_id: UUID,
        source_type: str,
        source_identifier: str
    ) -> List[ContextChunk]:
        """
        Procesa un texto completo:
        1. Lo divide en chunks semánticamente coherentes
        2. Genera embeddings para cada chunk con manejo de errores
        3. Almacena los chunks y embeddings en la base de datos
        """
        chunks = self.create_chunks(text)
        stored_chunks = []
        
        for chunk_text in chunks:
            try:
                embedding = await self.generate_embedding(chunk_text)
                
                chunk_data = ChunkCreate(
                    project_id=project_id,
                    user_id=user_id,
                    content_text=chunk_text,
                    content_embedding=embedding,
                    source_type=source_type,
                    source_identifier=source_identifier
                )
                
                chunk = await create_context_chunk(self.db, chunk_data)
                stored_chunks.append(chunk)
                
            except EmbeddingError as e:
                logger.error(f"Error al procesar chunk: {str(e)}")
                # Continuamos con el siguiente chunk en caso de error
                continue

        return stored_chunks

    async def find_relevant_context(
        self,
        query: str,
        project_id: UUID,
        user_id: Optional[UUID] = None,
        top_k: int = 5,
        similarity_threshold: Optional[float] = 0.3
    ) -> List[ChunkWithSimilarity]:
        """
        Encuentra los chunks más relevantes para una consulta dada.
        
        Args:
            query: Texto de la consulta
            project_id: ID del proyecto para filtrar
            user_id: ID del usuario para filtrar (opcional)
            top_k: Número de resultados a retornar
            similarity_threshold: Umbral mínimo de similitud (0 a 1)
        
        Returns:
            Lista de chunks con sus puntuaciones de similitud
        """
        try:
            # Generamos el embedding de la consulta
            query_embedding = await self.generate_embedding(query)
            
            # Buscamos chunks similares
            similar_chunks = await find_similar_chunks(
                self.db,
                query_embedding,
                project_id,
                user_id,
                top_k,
                similarity_threshold
            )
            
            # Calculamos similitudes y creamos respuesta
            chunks_with_similarity = []
            for chunk in similar_chunks:
                # Calculamos similitud coseno entre query_embedding y chunk.content_embedding
                similarity = self._calculate_cosine_similarity(
                    query_embedding,
                    chunk.content_embedding
                )
                
                chunks_with_similarity.append(
                    ChunkWithSimilarity(
                        chunk=chunk,
                        similarity_score=similarity
                    )
                )
            
            # Ordenamos por similitud descendente
            chunks_with_similarity.sort(key=lambda x: x.similarity_score, reverse=True)
            
            return chunks_with_similarity
            
        except EmbeddingError as e:
            logger.error(f"Error al buscar contexto relevante: {str(e)}")
            raise
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calcula la similitud coseno entre dos vectores.
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        return dot_product / (norm1 * norm2)

    def _count_tokens(self, text: str) -> int:
        """
        Cuenta el número de tokens en un texto usando tiktoken.
        """
        return len(self.tokenizer.encode(text))

    def _truncate_text_to_token_limit(self, text: str, max_tokens: int) -> str:
        """
        Trunca un texto para que no exceda el límite de tokens especificado.
        Intenta mantener oraciones completas.
        """
        if self._count_tokens(text) <= max_tokens:
            return text

        # Dividimos en oraciones
        sentences = text.split('. ')
        result = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence + '. ')
            if current_tokens + sentence_tokens > max_tokens:
                break
            result.append(sentence)
            current_tokens += sentence_tokens

        return '. '.join(result) + '.'

    async def generate_context_block(
        self,
        query: str,
        project_id: UUID,
        user_id: Optional[UUID] = None,
        max_tokens: Optional[int] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.3
    ) -> ContextBlock:
        """
        Genera un bloque de contexto coherente a partir de chunks relevantes.
        
        Args:
            query: Texto de la consulta
            project_id: ID del proyecto
            user_id: ID del usuario (opcional)
            max_tokens: Límite máximo de tokens (usa settings.MAX_CONTEXT_TOKENS si no se especifica)
            top_k: Número máximo de chunks a considerar
            similarity_threshold: Umbral mínimo de similitud
            
        Returns:
            ContextBlock con el texto combinado y metadatos
        """
        max_tokens = max_tokens or settings.MAX_CONTEXT_TOKENS
        effective_token_limit = max_tokens - settings.CONTEXT_TOKEN_BUFFER

        try:
            # Obtenemos chunks relevantes
            relevant_chunks = await self.find_relevant_context(
                query=query,
                project_id=project_id,
                user_id=user_id,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            if not relevant_chunks:
                return ContextBlock(
                    context_text="",
                    total_tokens=0,
                    chunks_used=0,
                    was_truncated=False
                )

            # Preparamos el texto combinado con separadores
            combined_texts = []
            total_tokens = 0
            chunks_used = 0
            was_truncated = False

            for chunk_with_sim in relevant_chunks:
                chunk_text = chunk_with_sim.chunk.content_text
                separator = settings.CONTEXT_SEPARATOR if combined_texts else ""
                next_addition = f"{separator}{chunk_text}"
                next_tokens = self._count_tokens(next_addition)

                # Verificamos si podemos añadir este chunk
                if total_tokens + next_tokens <= effective_token_limit:
                    combined_texts.append(next_addition)
                    total_tokens += next_tokens
                    chunks_used += 1
                else:
                    was_truncated = True
                    break

            # Combinamos todos los textos
            context_text = "".join(combined_texts)

            # Verificación final de límite de tokens
            if self._count_tokens(context_text) > max_tokens:
                context_text = self._truncate_text_to_token_limit(context_text, max_tokens)
                was_truncated = True

            return ContextBlock(
                context_text=context_text,
                total_tokens=self._count_tokens(context_text),
                chunks_used=chunks_used,
                was_truncated=was_truncated
            )

        except Exception as e:
            logger.error(f"Error al generar bloque de contexto: {str(e)}")
            raise 