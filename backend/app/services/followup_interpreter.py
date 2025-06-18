import json
import re
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import openai
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.models import InteractionEvent, ModeratedSynthesis
from app.schemas.query import QueryRequest, QueryType
from app.core.config import settings


class ContinuityAnalysis:
    """Análisis de continuidad conversacional."""
    
    def __init__(
        self, 
        is_continuation: bool,
        reference_type: str,
        confidence_score: float,
        previous_interaction_id: Optional[UUID] = None,
        contextual_keywords: Optional[List[str]] = None
    ):
        self.is_continuation = is_continuation
        self.reference_type = reference_type  # "anaphoric", "topic_expansion", "clarification", "new_topic"
        self.confidence_score = confidence_score
        self.previous_interaction_id = previous_interaction_id
        self.contextual_keywords = contextual_keywords or []


class InteractionContext:
    """Contexto de interacción previa para continuidad conversacional."""
    
    def __init__(
        self,
        interaction_id: UUID,
        user_prompt: str,
        refined_prompt: Optional[str],
        synthesis_text: Optional[str],
        created_at: str
    ):
        self.interaction_id = interaction_id
        self.user_prompt = user_prompt
        self.refined_prompt = refined_prompt
        self.synthesis_text = synthesis_text
        self.created_at = created_at


class FollowUpInterpreter:
    """Servicio para detectar continuidad conversacional e integrar contexto histórico."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo-1106"
        self.temperature = 0.2  # Baja temperatura para consistencia en detección
    
    async def handle_followup(
        self,
        user_prompt: str,
        project_id: UUID,
        user_id: UUID,
        conversation_mode: str = "auto"
    ) -> QueryRequest:
        """
        Función principal que detecta continuidad y genera QueryRequest enriquecido.
        
        Args:
            user_prompt: Prompt del usuario actual
            project_id: ID del proyecto
            user_id: ID del usuario
            conversation_mode: Modo de conversación ('auto', 'continue', 'new')
            
        Returns:
            QueryRequest con prompt enriquecido si es continuación, o prompt original si es tema nuevo
        """
        # 1. Determinar continuidad basado en el modo seleccionado por el usuario
        if conversation_mode == "new":
            # Usuario seleccionó explícitamente "Nueva conversación"
            return QueryRequest(
                user_question=user_prompt,
                project_id=project_id,
                user_id=user_id,
                query_type=QueryType.CONTEXT_AWARE
            )
        elif conversation_mode == "continue":
            # Usuario seleccionó explícitamente "Continuar conversación"
            recent_interaction_id = await self._get_most_recent_interaction_id(project_id, user_id)
            if recent_interaction_id:
                interaction_context = await self.get_recent_interaction_context(
                    project_id, user_id, recent_interaction_id
                )
                if interaction_context:
                    enriched_prompt = self.enrich_prompt_with_history(
                        user_prompt, 
                        interaction_context.refined_prompt or interaction_context.user_prompt,
                        interaction_context.synthesis_text or ""
                    )
                    return QueryRequest(
                        user_question=enriched_prompt,
                        project_id=project_id,
                        user_id=user_id,
                        query_type=QueryType.FOLLOW_UP
                    )
        
        # 2. Modo automático - usar la lógica simplificada
        continuity_analysis = await self.analyze_query_continuity(user_prompt, project_id, user_id)
        
        # 2. Si es continuación, recuperar contexto y enriquecer
        if continuity_analysis.is_continuation and continuity_analysis.previous_interaction_id:
            interaction_context = await self.get_recent_interaction_context(
                project_id, user_id, continuity_analysis.previous_interaction_id
            )
            
            if interaction_context:
                enriched_prompt = self.enrich_prompt_with_history(
                    user_prompt, 
                    interaction_context.refined_prompt or interaction_context.user_prompt,
                    interaction_context.synthesis_text or ""
                )
                
                return QueryRequest(
                    user_question=enriched_prompt,
                    project_id=project_id,
                    user_id=user_id,
                    query_type=QueryType.FOLLOW_UP
                )
        
        # 3. Si no es continuación, devolver prompt original
        return QueryRequest(
            user_question=user_prompt,
            project_id=project_id,
            user_id=user_id,
            query_type=QueryType.CONTEXT_AWARE
        )
    
    async def analyze_query_continuity(
        self,
        user_prompt: str,
        project_id: UUID,
        user_id: UUID
    ) -> ContinuityAnalysis:
        """
        Analiza si una consulta es continuación de una interacción previa.
        
        SIMPLIFICADO: Siempre asume continuidad si hay interacciones previas,
        a menos que el usuario seleccione explícitamente "Nueva conversación" en el frontend.
        """
        # Verificar si hay interacciones previas
        recent_interaction_id = await self._get_most_recent_interaction_id(project_id, user_id)
        
        if not recent_interaction_id:
            # No hay interacciones previas - definitivamente es tema nuevo
            return ContinuityAnalysis(
                is_continuation=False,
                reference_type="new_topic",
                confidence_score=1.0
            )
        
        # Hay interacciones previas - asumir continuidad por defecto
        # El usuario puede cambiar esto usando el ConversationModeToggle en el frontend
        return ContinuityAnalysis(
            is_continuation=True,
            reference_type="topic_expansion",  # Tipo genérico para continuidad
            confidence_score=0.8,  # Alta confianza en la decisión
            previous_interaction_id=recent_interaction_id,
            contextual_keywords=["continuidad_automatica"]
        )
    
    def _analyze_heuristic_patterns(self, user_prompt: str) -> Dict:
        """
        Análisis heurístico basado en patrones lingüísticos.
        
        Detecta referencias anafóricas y palabras clave de continuidad.
        """
        prompt_lower = user_prompt.lower().strip()
        
        # Patrones de continuidad fuerte (alta confianza)
        strong_continuation_patterns = [
            r'\b(eso|esto|lo anterior|lo que dijiste|la respuesta anterior)\b',
            r'(¿y si|pero qué tal si|y también|además)',
            r'\b(mejora eso|mejóralo|dame más detalles|amplía)\b',
            r'\b(los últimos \d+|lo último|la última vez)\b',
            r'\b(después de eso|luego|también considera)\b',
            r'(¿qué|¿cuál|¿cómo).*(algoritmo|método|técnica|enfoque|estrategia)',
            r'(¿qué|¿cuál).*(usar|utilizar|aplicar|implementar)',
            r'(¿cómo).*(hacer|implementar|desarrollar|crear)'
        ]
        
        # Patrones de continuidad débil (requieren análisis LLM)
        weak_continuation_patterns = [
            r'\b(otra opción|alternativa|diferente)\b',
            r'\b(también|igualmente|parecido)\b',
            r'\b(pero|sin embargo|aunque)\b'
        ]
        
        # Patrones de tema nuevo
        new_topic_patterns = [
            r'\b(nueva consulta|cambio de tema|ahora quiero)\b',
            r'\b(por otro lado|completamente diferente)\b'
        ]
        
        # Verificar patrones fuertes de continuidad
        for pattern in strong_continuation_patterns:
            if re.search(pattern, prompt_lower):
                return {
                    "is_continuation": True,
                    "reference_type": "anaphoric",
                    "confidence": 0.9,
                    "keywords": re.findall(pattern, prompt_lower)
                }
        
        # Verificar patrones de tema nuevo
        for pattern in new_topic_patterns:
            if re.search(pattern, prompt_lower):
                return {
                    "is_continuation": False,
                    "reference_type": "new_topic",
                    "confidence": 0.9,
                    "keywords": re.findall(pattern, prompt_lower)
                }
        
        # Verificar patrones débiles
        for pattern in weak_continuation_patterns:
            if re.search(pattern, prompt_lower):
                return {
                    "is_continuation": True,
                    "reference_type": "topic_expansion",
                    "confidence": 0.4,  # Baja confianza, requiere análisis LLM
                    "keywords": re.findall(pattern, prompt_lower)
                }
        
        # Sin patrones detectados - probablemente tema nuevo
        return {
            "is_continuation": False,
            "reference_type": "new_topic",
            "confidence": 0.6,
            "keywords": []
        }
    
    async def _analyze_with_llm(self, user_prompt: str, recent_interaction: InteractionContext) -> Dict:
        """
        Análisis con LLM para casos ambiguos.
        """
        system_prompt = """Eres un experto en análisis conversacional. Tu tarea es determinar si una nueva consulta del usuario es continuación de una consulta anterior o un tema completamente nuevo.

Responde en JSON válido con estos campos:
- is_continuation: boolean (true si es continuación, false si es tema nuevo)
- reference_type: string ("anaphoric", "topic_expansion", "clarification", "new_topic")
- confidence: float (0.0 a 1.0, donde 1.0 es máxima confianza)
- keywords: lista de strings (palabras clave que indican la relación)

Criterios:
- CONTINUACIÓN: Referencias pronominales, ampliación del mismo tema, modificaciones o condiciones sobre el tema anterior
- TEMA NUEVO: Dominio completamente diferente, sin relación semántica con la consulta anterior"""

        user_message = f"""
CONSULTA ANTERIOR:
{recent_interaction.user_prompt}

SÍNTESIS PREVIA:
{recent_interaction.synthesis_text[:300] if recent_interaction.synthesis_text else "Sin síntesis disponible"}

NUEVA CONSULTA:
{user_prompt}

¿Es la nueva consulta una continuación de la anterior?"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            
            return {
                "is_continuation": result.get("is_continuation", False),
                "reference_type": result.get("reference_type", "new_topic"),
                "confidence": result.get("confidence", 0.5),
                "keywords": result.get("keywords", [])
            }
            
        except Exception as e:
            # Fallback en caso de error
            return {
                "is_continuation": False,
                "reference_type": "new_topic",
                "confidence": 0.3,
                "keywords": []
            }
    
    async def get_recent_interaction_context(
        self,
        project_id: UUID,
        user_id: UUID,
        interaction_id: Optional[UUID] = None
    ) -> Optional[InteractionContext]:
        """
        Recupera el contexto de la interacción más reciente o específica.
        """
        if interaction_id:
            # Buscar interacción específica
            stmt = select(InteractionEvent, ModeratedSynthesis).outerjoin(
                ModeratedSynthesis, InteractionEvent.moderated_synthesis_id == ModeratedSynthesis.id
            ).where(
                InteractionEvent.id == interaction_id,
                InteractionEvent.project_id == project_id,
                InteractionEvent.user_id == user_id
            )
        else:
            # Buscar interacción más reciente
            stmt = select(InteractionEvent, ModeratedSynthesis).outerjoin(
                ModeratedSynthesis, InteractionEvent.moderated_synthesis_id == ModeratedSynthesis.id
            ).where(
                InteractionEvent.project_id == project_id,
                InteractionEvent.user_id == user_id
            ).order_by(InteractionEvent.created_at.desc()).limit(1)
        
        result = await self.db.exec(stmt)
        row = result.first()
        
        if not row:
            return None
        
        interaction_event, moderated_synthesis = row
        
        # Extraer refined_prompt del JSON si existe
        refined_prompt = None
        if interaction_event.ai_responses_json:
            try:
                ai_responses = json.loads(interaction_event.ai_responses_json)
                # Buscar refined_prompt en los metadatos
                if isinstance(ai_responses, dict) and "refined_prompt" in ai_responses:
                    refined_prompt = ai_responses["refined_prompt"]
            except:
                pass
        
        return InteractionContext(
            interaction_id=interaction_event.id,
            user_prompt=interaction_event.user_prompt_text,
            refined_prompt=refined_prompt,
            synthesis_text=moderated_synthesis.synthesis_text if moderated_synthesis else None,
            created_at=interaction_event.created_at.isoformat()
        )
    
    async def _get_most_recent_interaction_id(self, project_id: UUID, user_id: UUID) -> Optional[UUID]:
        """Obtiene el ID de la interacción más reciente."""
        stmt = select(InteractionEvent.id).where(
            InteractionEvent.project_id == project_id,
            InteractionEvent.user_id == user_id
        ).order_by(InteractionEvent.created_at.desc()).limit(1)
        
        result = await self.db.exec(stmt)
        return result.first()
    
    async def _get_most_recent_interaction(self, project_id: UUID, user_id: UUID) -> Optional[InteractionContext]:
        """Obtiene la interacción más reciente completa."""
        return await self.get_recent_interaction_context(project_id, user_id)
    
    def enrich_prompt_with_history(
        self,
        current_prompt: str,
        previous_prompt: str,
        previous_synthesis: str
    ) -> str:
        """
        Enriquece el prompt actual con contexto histórico.
        
        Args:
            current_prompt: Prompt actual del usuario
            previous_prompt: Prompt refinado de la interacción anterior
            previous_synthesis: Síntesis del moderador de la interacción anterior
            
        Returns:
            Prompt enriquecido con contexto histórico
        """
        # Limitar la síntesis para no exceder límites de tokens
        max_synthesis_chars = 800
        truncated_synthesis = previous_synthesis[:max_synthesis_chars]
        if len(previous_synthesis) > max_synthesis_chars:
            truncated_synthesis += "..."
        
        enriched_prompt = f"""CONTEXTO PREVIO (para referencia):
Consulta anterior: {previous_prompt}
Síntesis proporcionada: {truncated_synthesis}

NUEVA CONSULTA (amplía o modifica lo anterior):
{current_prompt}

INSTRUCCIÓN: Responde considerando el contexto previo pero enfócate en la nueva consulta. Si la nueva consulta hace referencia a "eso", "lo anterior", "mejora", etc., usa la información del contexto previo para entender a qué se refiere."""

        return enriched_prompt


# Función de utilidad para crear instancia del servicio
def create_followup_interpreter(db: AsyncSession) -> FollowUpInterpreter:
    """Factory function para crear una instancia de FollowUpInterpreter."""
    return FollowUpInterpreter(db)