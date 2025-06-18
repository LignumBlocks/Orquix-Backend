from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
import asyncio
import logging
from datetime import datetime
import numpy as np
import tiktoken

from openai import AsyncOpenAI
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.models import ContextChunk, InteractionEvent, ModeratedSynthesis
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

    async def get_recent_conversation_history(
        self,
        project_id: UUID,
        user_id: UUID,
        limit: int = 3,
        max_tokens_per_item: int = 200
    ) -> List[Dict[str, str]]:
        """
        Recupera el historial conversacional reciente del usuario en un proyecto.
        
        Args:
            project_id: ID del proyecto
            user_id: ID del usuario
            limit: Número máximo de interacciones a recuperar
            max_tokens_per_item: Tokens máximos por elemento del historial
            
        Returns:
            Lista de diccionarios con user_prompt y moderator_response
        """
        try:
            # Query para obtener interacciones recientes con síntesis moderada
            query = (
                select(InteractionEvent, ModeratedSynthesis.synthesis_text)
                .outerjoin(ModeratedSynthesis, InteractionEvent.moderated_synthesis_id == ModeratedSynthesis.id)
                .where(
                    InteractionEvent.project_id == project_id,
                    InteractionEvent.user_id == user_id,
                    InteractionEvent.deleted_at.is_(None)
                )
                .order_by(InteractionEvent.created_at.desc())
                .limit(limit)
            )
            
            result = await self.db.execute(query)
            rows = result.all()
            
            history = []
            for interaction_event, synthesis_text in rows:
                # Truncar el prompt del usuario si es muy largo
                user_prompt = interaction_event.user_prompt_text
                if self._count_tokens(user_prompt) > max_tokens_per_item:
                    user_prompt = self._truncate_text_to_token_limit(user_prompt, max_tokens_per_item)
                
                # Obtener respuesta del moderador
                moderator_response = ""
                if synthesis_text:
                    moderator_response = synthesis_text
                    if self._count_tokens(moderator_response) > max_tokens_per_item:
                        moderator_response = self._truncate_text_to_token_limit(moderator_response, max_tokens_per_item)
                
                history.append({
                    "user_prompt": user_prompt,
                    "moderator_response": moderator_response,
                    "timestamp": interaction_event.created_at.isoformat()
                })
            
            # Invertir el orden para tener el más antiguo primero
            return list(reversed(history))
            
        except Exception as e:
            logger.error(f"Error al recuperar historial conversacional: {str(e)}")
            return []

    def format_conversation_history(
        self,
        history: List[Dict[str, str]],
        max_total_tokens: int = 800
    ) -> str:
        """
        Formatea el historial conversacional en un texto coherente.
        
        Args:
            history: Lista de interacciones del historial
            max_total_tokens: Tokens máximos para todo el historial formateado
            
        Returns:
            Texto formateado del historial
        """
        if not history:
            return ""
        
        formatted_parts = []
        current_tokens = 0
        
        # Agregar header
        header = "Historial de conversación reciente:"
        formatted_parts.append(header)
        current_tokens += self._count_tokens(header)
        
        # Procesar cada interacción
        for i, interaction in enumerate(history):
            user_part = f"\nUsuario: {interaction['user_prompt']}"
            moderator_part = f"\nModerador: {interaction['moderator_response']}" if interaction['moderator_response'] else ""
            
            interaction_text = user_part + moderator_part
            interaction_tokens = self._count_tokens(interaction_text)
            
            # Verificar si podemos agregar esta interacción
            if current_tokens + interaction_tokens <= max_total_tokens:
                formatted_parts.append(interaction_text)
                current_tokens += interaction_tokens
            else:
                # Si no cabe, truncar esta interacción para que quepa
                remaining_tokens = max_total_tokens - current_tokens - 50  # Buffer de seguridad
                if remaining_tokens > 100:  # Solo si queda espacio razonable
                    truncated_interaction = self._truncate_text_to_token_limit(
                        interaction_text, 
                        remaining_tokens
                    )
                    formatted_parts.append(truncated_interaction)
                break
        
        # Agregar separador final
        formatted_parts.append("\n---\n")
        
        return "".join(formatted_parts)

    async def enrich_query_with_history(
        self,
        query: str,
        project_id: UUID,
        user_id: UUID,
        enable_history: bool = True,
        max_history_tokens: int = 600
    ) -> str:
        """
        Enriquece una consulta con historial conversacional si es necesario.
        
        Args:
            query: Consulta original del usuario
            project_id: ID del proyecto
            user_id: ID del usuario
            enable_history: Si incluir historial (configurable)
            max_history_tokens: Tokens máximos para el historial
            
        Returns:
            Query enriquecida con historial o query original
        """
        if not enable_history:
            return query
        
        # Verificar si la query parece necesitar contexto histórico
        if not self._query_needs_history(query):
            return query
        
        try:
            # Obtener historial reciente
            history = await self.get_recent_conversation_history(
                project_id=project_id,
                user_id=user_id,
                limit=3
            )
            
            if not history:
                return query
            
            # Formatear historial
            formatted_history = self.format_conversation_history(
                history=history,
                max_total_tokens=max_history_tokens
            )
            
            # Construir query enriquecida
            enriched_query = f"{formatted_history}Nueva pregunta: {query}"
            
            logger.info(f"Query enriquecida con historial de {len(history)} interacciones")
            return enriched_query
            
        except Exception as e:
            logger.error(f"Error al enriquecer query con historial: {str(e)}")
            return query  # Fallback a query original

    def _query_needs_history(self, query: str) -> bool:
        """
        Determina si una consulta probablemente necesita historial conversacional.
        Busca patrones de referencias implícitas.
        """
        query_lower = query.lower().strip()
        
        # Patrones que indican referencias implícitas
        implicit_patterns = [
            # Referencias directoriales 
            "últimos", "primeros", "anteriores", "previos",
            
            # Pronombres y referencias 
            "eso", "esto", "esos", "estas", "aquello", "lo que",
            "el que", "la que", "los que", "las que",
            
            # Referencias temporales implícitas
            "antes", "después", "luego", "ahora", "ya",
            
            # Acciones sobre contenido previo
            "mejora", "cambia", "modifica", "ajusta", "corrige",
            "amplía", "resume", "explica", "detalla",
            
            # Referencias numéricas sin contexto
            "los 4", "las 5", "los 3", "dame 2",
            
            # Comparaciones implícitas
            "mejor", "peor", "similar", "parecido", "como",
            
            # Referencias a resultados previos
            "resultado", "respuesta", "lo anterior", "arriba"
        ]
        
        # Verificar si contiene algún patrón
        for pattern in implicit_patterns:
            if pattern in query_lower:
                return True
        
        # Verificar queries muy cortas (probable referencia implícita)
        # Pero excluir preguntas completas con palabras interrogativas
        words = query.split()
        if len(words) <= 3:
            # Excluir preguntas que empiecen con palabras interrogativas completas
            interrogative_words = ["qué", "que", "cómo", "como", "cuándo", "cuando", "dónde", "donde", "por", "para", "quién", "quien"]
            first_word = words[0].lower().strip("¿?")
            if first_word not in interrogative_words:
                return True
            
        return False

    async def get_recent_interaction_context(
        self,
        project_id: UUID,
        user_id: UUID,
        max_interactions: int = 1
    ) -> List[Dict[str, str]]:
        """
        Recupera el contexto de las interacciones más recientes para continuidad conversacional.
        
        Esta función es específica para el FollowUpInterpreter y complementa la funcionalidad
        de get_recent_conversation_history() con un formato simplificado.
        
        Args:
            project_id: ID del proyecto
            user_id: ID del usuario
            max_interactions: Número máximo de interacciones a recuperar
            
        Returns:
            Lista de diccionarios con información de las interacciones recientes
        """
        import json
        from app.models.models import ModeratedSynthesis
        
        try:
            # Query para obtener las interacciones más recientes con sus síntesis
            stmt = select(InteractionEvent, ModeratedSynthesis).outerjoin(
                ModeratedSynthesis, InteractionEvent.moderated_synthesis_id == ModeratedSynthesis.id
            ).where(
                InteractionEvent.project_id == project_id,
                InteractionEvent.user_id == user_id,
                InteractionEvent.deleted_at.is_(None)
            ).order_by(InteractionEvent.created_at.desc()).limit(max_interactions)
            
            result = await self.db.exec(stmt)
            rows = result.all()
            
            interactions_context = []
            
            for interaction_event, moderated_synthesis in rows:
                # Extraer refined_prompt del JSON si existe
                refined_prompt = None
                if interaction_event.ai_responses_json:
                    try:
                        ai_responses = json.loads(interaction_event.ai_responses_json)
                        if isinstance(ai_responses, dict) and "refined_prompt" in ai_responses:
                            refined_prompt = ai_responses["refined_prompt"]
                    except:
                        pass
                
                interaction_context = {
                    "interaction_id": str(interaction_event.id),
                    "user_prompt": interaction_event.user_prompt_text,
                    "refined_prompt": refined_prompt or interaction_event.user_prompt_text,
                    "synthesis": moderated_synthesis.synthesis_text if moderated_synthesis else "",
                    "created_at": interaction_event.created_at.isoformat()
                }
                
                interactions_context.append(interaction_context)
            
            return interactions_context
            
        except Exception as e:
            logger.error(f"Error al recuperar contexto de interacciones recientes: {str(e)}")
            return [] 