import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import openai
from app.core.config import settings
from app.models.context_session import (
    ContextMessage, 
    ContextChatResponse,
    ContextSession
)

logger = logging.getLogger(__name__)

class ContextBuilderService:
    """
    Servicio para construcción conversacional de contexto usando GPT-3.5.
    
    Este servicio ayuda a los usuarios a construir contexto de manera fluida
    antes de enviar consultas a las IAs principales.
    """
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.3  # Más determinístico para consistencia
        self.max_tokens = 500   # Respuestas concisas
    
    async def process_user_message(
        self,
        user_message: str,
        conversation_history: List[ContextMessage],
        current_context: str
    ) -> ContextChatResponse:
        """
        Procesa un mensaje del usuario y genera una respuesta apropiada.
        
        Args:
            user_message: Mensaje del usuario
            conversation_history: Historial de la conversación
            current_context: Contexto acumulado hasta ahora
            
        Returns:
            ContextChatResponse con la respuesta y metadatos
        """
        try:
            # Construir prompt para GPT-3.5
            system_prompt = self._build_system_prompt()
            messages = self._build_conversation_messages(
                system_prompt, user_message, conversation_history, current_context
            )
            
            # Llamar a GPT-3.5
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parsear respuesta JSON
            response_content = response.choices[0].message.content
            parsed_response = json.loads(response_content)
            
            # Extraer información
            message_type = parsed_response.get("message_type", "question")
            ai_response = parsed_response.get("response_text", "")
            context_update = parsed_response.get("context_update", "")
            suggestions = parsed_response.get("suggestions", [])
            suggested_final_question = parsed_response.get("suggested_final_question", "")
            
            # Actualizar contexto acumulado si hay nueva información
            updated_context = current_context
            if message_type == "information" and context_update:
                updated_context = self._update_accumulated_context(
                    current_context, context_update
                )
            
            # Evaluar si el contexto está listo para finalizar
            if message_type != "ready" and self._should_suggest_finalization(updated_context):
                message_type = "ready"
                if not suggested_final_question:
                    suggested_final_question = self._generate_suggested_question(updated_context, user_message)
                ai_response = f"{ai_response}\n\n🎯 **Contexto completado!** Te sugiero esta pregunta para las IAs principales: \"{suggested_final_question}\""
                suggestions = ["Usa la pregunta sugerida", "Modifica la pregunta si lo necesitas", "Agrega más contexto si falta algo"]
            
            # Contar elementos de contexto
            context_elements = self._count_context_elements(updated_context)
            
            return ContextChatResponse(
                session_id=uuid4(),  # Se actualizará con el ID real en el endpoint
                ai_response=ai_response,
                message_type=message_type,
                accumulated_context=updated_context,
                suggestions=suggestions,
                context_elements_count=context_elements,
                suggested_final_question=suggested_final_question if message_type == "ready" else None
            )
            
        except openai.APIError as e:
            logger.error(f"Error de API de OpenAI: {e}")
            return self._create_fallback_response(user_message, current_context)
        except openai.RateLimitError as e:
            logger.error(f"Rate limit excedido en OpenAI: {e}")
            return self._create_fallback_response(user_message, current_context)
        except json.JSONDecodeError as e:
            logger.warning(f"Error parsing GPT-3.5 response, reintentando con fallback: {e}")
            # Intentar una segunda vez con un prompt más simple
            try:
                simple_response = await self._simple_gpt_call(user_message, current_context)
                return simple_response
            except Exception:
                return self._create_fallback_response(user_message, current_context)
        except Exception as e:
            logger.error(f"Error inesperado en context builder: {e}")
            return self._create_fallback_response(user_message, current_context)
    
    def _build_system_prompt(self) -> str:
        """Construye el prompt del sistema para GPT-3.5."""
        return """
Eres un asistente especializado en ayudar a usuarios a construir contexto para consultas complejas.

Tu rol es:
1. IDENTIFICAR si el usuario está:
   - PREGUNTANDO algo (necesita información/clarificación)
   - APORTANDO información (agregando al contexto del proyecto)

2. ACUMULAR información relevante para el contexto del proyecto

3. GUIAR al usuario para obtener información completa y útil

4. SUGERIR FINALIZACIÓN cuando el contexto esté completo con una pregunta específica

INSTRUCCIONES IMPORTANTES:
- Sé conversacional y natural
- Haz preguntas específicas para obtener detalles útiles
- Reconoce cuando el usuario aporta información valiosa
- Sugiere áreas importantes que podrían faltar
- Mantén un tono profesional pero amigable
- Cuando el contexto esté completo (3+ elementos o 50+ palabras), sugiere una pregunta específica

Responde SIEMPRE en este formato JSON válido:
{
  "message_type": "question|information|ready",
  "response_text": "Tu respuesta conversacional al usuario",
  "context_update": "Información específica a agregar al contexto (solo si message_type es 'information')",
  "suggestions": ["Sugerencia 1", "Sugerencia 2"],
  "suggested_final_question": "Pregunta específica sugerida para las IAs principales (solo si message_type es 'ready')"
}

Tipos de message_type:
- "question": El usuario hizo una pregunta o necesita orientación
- "information": El usuario aportó información útil para el contexto
- "ready": El contexto parece completo y listo para enviar a IAs principales (incluye suggested_final_question)
"""
    
    def _build_conversation_messages(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[ContextMessage],
        current_context: str
    ) -> List[Dict[str, str]]:
        """Construye los mensajes para enviar a GPT-3.5."""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Agregar contexto actual si existe
        if current_context.strip():
            context_info = f"""
CONTEXTO ACTUAL DEL PROYECTO:
{current_context}

---
"""
            messages.append({"role": "system", "content": context_info})
        
        # Agregar historial de conversación (últimos 6 mensajes para no exceder límites)
        recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
        for msg in recent_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Agregar mensaje actual del usuario
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _update_accumulated_context(self, current_context: str, new_info: str) -> str:
        """Actualiza el contexto acumulado con nueva información."""
        if not current_context.strip():
            return new_info.strip()
        
        # Evitar duplicación
        if new_info.strip() in current_context:
            return current_context
        
        # Agregar nueva información
        return f"{current_context}\n\n• {new_info.strip()}"
    
    def _count_context_elements(self, context: str) -> int:
        """Cuenta los elementos en el contexto acumulado."""
        if not context.strip():
            return 0
        
        # Contar líneas que comienzan con bullet points o que tienen contenido sustancial
        lines = [line.strip() for line in context.split('\n') if line.strip()]
        elements = [line for line in lines if line.startswith('•') or len(line) > 10]
        return len(elements)
    
    def _create_fallback_response(
        self, 
        user_message: str, 
        current_context: str
    ) -> ContextChatResponse:
        """Crea una respuesta de fallback en caso de error con OpenAI."""
        
        # Fallback inteligente sin palabras clave - usar análisis de estructura
        is_question = self._analyze_message_structure(user_message)
        
        if is_question:
            # Es una pregunta
            updated_context = current_context
            if not current_context.strip():
                response_text = "¡Hola! Estoy aquí para ayudarte a construir el contexto de tu consulta. ¿Podrías contarme más sobre tu proyecto o situación?"
            else:
                response_text = "Entiendo tu pregunta. ¿Podrías darme más detalles específicos para poder ayudarte mejor?"
            
            suggestions = [
                "Describe tu proyecto o empresa",
                "Comparte los principales desafíos",
                "Explica qué tipo de ayuda necesitas"
            ]
            message_type = "question"
            context_elements = self._count_context_elements(updated_context)
        else:
            # Es información
            updated_context = self._update_accumulated_context(current_context, user_message)
            response_text = "Perfecto, he registrado esa información. ¿Hay algo más que quieras agregar sobre tu proyecto?"
            suggestions = [
                "Comparte más detalles sobre tu negocio",
                "Describe tus principales desafíos",
                "Háblame de tus objetivos"
            ]
            message_type = "information"
            context_elements = self._count_context_elements(updated_context)
        
        # Evaluar si está listo para finalizar
        if self._should_suggest_finalization(updated_context):
            message_type = "ready"
            suggested_question = self._generate_suggested_question(updated_context, user_message)
            response_text = f"{response_text}\n\n🎯 **Contexto completado!** Te sugiero esta pregunta para las IAs principales: \"{suggested_question}\""
            suggestions = ["Usa la pregunta sugerida", "Modifica la pregunta si lo necesitas", "Agrega más contexto si falta algo"]
        else:
            suggested_question = None
        
        return ContextChatResponse(
            session_id=uuid4(),
            ai_response=response_text,
            message_type=message_type,
            accumulated_context=updated_context,
            suggestions=suggestions,
            context_elements_count=context_elements,
            suggested_final_question=suggested_question
        )
    
    def _analyze_message_structure(self, message: str) -> bool:
        """
        Analiza la estructura del mensaje para determinar si es una pregunta.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            True si parece ser una pregunta, False si parece ser información
        """
        message_lower = message.lower().strip()
        
        # Indicadores claros de pregunta
        question_indicators = [
            message.startswith('¿'),
            message.endswith('?'),
            any(word in message_lower for word in ['cómo', 'qué', 'cuál', 'cuándo', 'dónde', 'por qué', 'quién']),
            any(word in message_lower for word in ['ayuda', 'necesito ayuda', 'puedes', 'podrías']),
            message_lower.startswith('me puedes'),
            message_lower.startswith('podrías'),
            message_lower.startswith('necesito'),
        ]
        
        # Indicadores claros de información
        info_indicators = [
            any(word in message_lower for word in ['tengo', 'somos', 'estamos', 'operamos', 'tenemos']),
            any(word in message_lower for word in ['mi empresa', 'mi startup', 'nuestro', 'nuestra']),
            any(word in message_lower for word in ['soy', 'trabajo en', 'me dedico']),
            message_lower.startswith('el proyecto'),
            message_lower.startswith('la empresa'),
            message_lower.startswith('mi'),
            message_lower.startswith('nuestro'),
            message_lower.startswith('nuestra'),
        ]
        
        # Contar indicadores
        question_score = sum(question_indicators)
        info_score = sum(info_indicators)
        
        # Si hay indicadores claros, usarlos
        if question_score > info_score:
            return True
        elif info_score > question_score:
            return False
        
        # Si no hay indicadores claros, usar heurísticas adicionales
        # Las preguntas tienden a ser más cortas y menos descriptivas
        word_count = len(message.split())
        
        # Mensajes muy cortos con palabras de acción tienden a ser preguntas
        if word_count <= 5 and any(word in message_lower for word in ['ayuda', 'necesito', 'quiero', 'puedo']):
            return True
        
        # Mensajes largos y descriptivos tienden a ser información
        if word_count > 15:
            return False
        
        # Por defecto, asumir que es una pregunta para ser más interactivo
        return True
    
    def _should_suggest_finalization(self, context: str) -> bool:
        """
        Evalúa si el contexto está listo para finalizar automáticamente.
        
        Args:
            context: Contexto acumulado
            
        Returns:
            True si el contexto parece completo
        """
        if not context.strip():
            return False
        
        # Criterios para sugerir finalización
        element_count = self._count_context_elements(context)
        word_count = len(context.split())
        
        # Sugerir finalización si hay suficiente información
        return element_count >= 3 or word_count >= 50
    
    def _generate_suggested_question(self, context: str, last_message: str) -> str:
        """
        Genera una pregunta sugerida basada en el contexto acumulado.
        
        Args:
            context: Contexto acumulado
            last_message: Último mensaje del usuario
            
        Returns:
            Pregunta sugerida para las IAs principales
        """
        # Analizar el contexto para generar una pregunta relevante
        context_lower = context.lower()
        last_message_lower = last_message.lower()
        
        # Detectar temas principales
        if any(word in context_lower for word in ['empresa', 'negocio', 'startup', 'compañía']):
            if any(word in context_lower for word in ['marketing', 'ventas', 'clientes']):
                return "¿Cómo puedo mejorar mi estrategia de marketing y ventas basándome en mi situación actual?"
            elif any(word in context_lower for word in ['tecnología', 'desarrollo', 'software', 'app']):
                return "¿Qué recomendaciones tecnológicas me darías para mi proyecto?"
            elif any(word in context_lower for word in ['financiero', 'inversión', 'dinero', 'capital']):
                return "¿Qué opciones financieras y de inversión serían más adecuadas para mi situación?"
            else:
                return "¿Qué estrategias y recomendaciones me sugieres para hacer crecer mi negocio?"
        
        elif any(word in context_lower for word in ['proyecto', 'idea', 'plan']):
            return "¿Cómo puedo desarrollar y ejecutar exitosamente este proyecto?"
        
        elif any(word in context_lower for word in ['problema', 'desafío', 'dificultad']):
            return "¿Cuáles serían las mejores soluciones para resolver estos desafíos?"
        
        else:
            # Pregunta genérica basada en el último mensaje
            if '?' in last_message:
                return last_message.strip()
            else:
                return f"¿Puedes ayudarme con {last_message.lower().strip()}?"
    
    async def suggest_finalization(self, context: str) -> bool:
        """
        Evalúa si el contexto está listo para finalizar.
        
        Args:
            context: Contexto acumulado
            
        Returns:
            True si el contexto parece completo
        """
        if not context.strip():
            return False
        
        # Criterios simples para sugerir finalización
        element_count = self._count_context_elements(context)
        word_count = len(context.split())
        
        # Sugerir finalización si hay suficiente información
        return element_count >= 3 or word_count >= 50
    
    async def _simple_gpt_call(self, user_message: str, current_context: str) -> ContextChatResponse:
        """
        Llamada simplificada a GPT-3.5 cuando falla el parsing JSON.
        
        Args:
            user_message: Mensaje del usuario
            current_context: Contexto actual
            
        Returns:
            ContextChatResponse con respuesta simple
        """
        simple_prompt = f"""
Analiza este mensaje del usuario y responde si es una PREGUNTA o INFORMACIÓN.

Mensaje: "{user_message}"
Contexto actual: "{current_context}"

Responde SOLO con este formato JSON:
{{"message_type": "question", "response_text": "Tu respuesta aquí"}}

Si es información, usa "information" como message_type.
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": simple_prompt}],
            temperature=0.1,
            max_tokens=200
        )
        
        response_content = response.choices[0].message.content.strip()
        
        # Intentar parsear JSON simple
        try:
            parsed = json.loads(response_content)
            message_type = parsed.get("message_type", "question")
            ai_response = parsed.get("response_text", "¿Podrías darme más detalles?")
        except:
            # Si falla, usar análisis de estructura
            message_type = "question" if self._analyze_message_structure(user_message) else "information"
            ai_response = "Entiendo. ¿Podrías contarme más detalles?" if message_type == "question" else "Perfecto, he registrado esa información."
        
        # Actualizar contexto si es información
        updated_context = current_context
        if message_type == "information":
            updated_context = self._update_accumulated_context(current_context, user_message)
        
        # Evaluar finalización
        suggested_question = None
        if self._should_suggest_finalization(updated_context):
            message_type = "ready"
            suggested_question = self._generate_suggested_question(updated_context, user_message)
            ai_response = f"{ai_response}\n\n🎯 **Contexto completado!** Te sugiero esta pregunta: \"{suggested_question}\""
        
        return ContextChatResponse(
            session_id=uuid4(),
            ai_response=ai_response,
            message_type=message_type,
            accumulated_context=updated_context,
            suggestions=["Continúa compartiendo información", "Haz preguntas específicas"],
            context_elements_count=self._count_context_elements(updated_context),
            suggested_final_question=suggested_question
        )

# Instancia global del servicio
context_builder_service = ContextBuilderService() 