import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import openai
from app.core.config import settings
from app.models.context_session import (
    ContextMessage, 
    ContextChatResponse,
    ContextSession
)

logger = logging.getLogger(__name__)

# Funciones helper fuera de la clase
async def classify_message_llm(
    client: openai.AsyncOpenAI,
    user_message: str,
    model: str = "gpt-3.5-turbo"
) -> Tuple[str, float]:
    """
    Clasifica un mensaje usando LLM de forma agnóstica al idioma.
    
    Args:
        client: Cliente de OpenAI
        user_message: Mensaje del usuario
        model: Modelo a usar
        
    Returns:
        Tuple con (message_type, confidence)
    """
    prompt = (
        "You are a language-agnostic classifier. "
        "Return ONLY valid JSON with keys: "
        "message_type ('question' or 'information') and confidence (0-1). "
        f"Text: «{user_message.strip()}»"
    )
    try:
        chat = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=50,
            response_format={"type": "json_object"}
        )
        data = json.loads(chat.choices[0].message.content)
        if data["message_type"] in ("question", "information"):
            return data["message_type"], float(data["confidence"])
    except Exception as e:
        logger.debug(f"LLM classify failed → fallback: {e}")
    return _fallback_heuristic(user_message)

def _fallback_heuristic(msg: str) -> Tuple[str, float]:
    """
    Heurística universal de fallback para clasificación.
    
    Args:
        msg: Mensaje a clasificar
        
    Returns:
        Tuple con (message_type, confidence)
    """
    text = msg.strip()
    if text.endswith("?") or (text.count("?") == 1 and len(text) < 80):
        return "question", 0.6
    if len(text.split()) > 15:
        return "information", 0.6
    return "question", 0.5

# Funciones helper fuera de la clase
async def classify_message_llm(
    client: openai.AsyncOpenAI,
    user_message: str,
    model: str = "gpt-3.5-turbo"
) -> Tuple[str, float]:
    """
    Clasifica un mensaje usando LLM de forma agnóstica al idioma.
    
    Args:
        client: Cliente de OpenAI
        user_message: Mensaje del usuario
        model: Modelo a usar
        
    Returns:
        Tuple con (message_type, confidence)
    """
    prompt = (
        "You are a language-agnostic classifier. "
        "Return ONLY valid JSON with keys: "
        "message_type ('question' or 'information') and confidence (0-1). "
        f"Text: «{user_message.strip()}»"
    )
    try:
        chat = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=50,
            response_format={"type": "json_object"}
        )
        data = json.loads(chat.choices[0].message.content)
        if data["message_type"] in ("question", "information"):
            return data["message_type"], float(data["confidence"])
    except Exception as e:
        logger.debug(f"LLM classify failed → fallback: {e}")
    return _fallback_heuristic(user_message)

def _fallback_heuristic(msg: str) -> Tuple[str, float]:
    """
    Heurística universal de fallback para clasificación.
    
    Args:
        msg: Mensaje a clasificar
        
    Returns:
        Tuple con (message_type, confidence)
    """
    text = msg.strip()
    if text.endswith("?") or (text.count("?") == 1 and len(text) < 80):
        return "question", 0.6
    if len(text.split()) > 15:
        return "information", 0.6
    return "question", 0.5

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
    
    async def _smart_classify(self, user_message: str) -> Tuple[str, float]:
        """
        Clasifica un mensaje usando LLM multilingüe con fallback universal.
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            Tuple con (message_type, confidence)
        """
        return await classify_message_llm(self.client, user_message, self.model)
    
    async def _smart_classify(self, user_message: str) -> Tuple[str, float]:
        """
        Clasifica un mensaje usando LLM multilingüe con fallback universal.
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            Tuple con (message_type, confidence)
        """
        return await classify_message_llm(self.client, user_message, self.model)
    
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
            # Clasificar el mensaje con el nuevo método
            message_type, confidence = await self._smart_classify(user_message)
            is_question = message_type == "question"
            
            # Si la confianza es baja, pedir aclaración
            if confidence < 0.55:
                return ContextChatResponse(
                    session_id=uuid4(),
                    ai_response="No estoy seguro de si eso es una pregunta o información. ¿Podrías aclararlo o aportar más detalles?",
                    message_type="question",
                    accumulated_context=current_context,
                    suggestions=["Reformula tu mensaje", "Sé más específico", "Agrega más contexto"],
                    context_elements_count=self._count_context_elements(current_context),
                    suggested_final_question=None
                )
            
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
            if context_update and context_update.strip():
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
            return await self._create_fallback_response(user_message, current_context)
        except openai.RateLimitError as e:
            logger.error(f"Rate limit excedido en OpenAI: {e}")
            return await self._create_fallback_response(user_message, current_context)
        except json.JSONDecodeError as e:
            logger.warning(f"Error parsing GPT-3.5 response, reintentando con fallback: {e}")
            # Intentar una segunda vez con un prompt más simple
            try:
                simple_response = await self._simple_gpt_call(user_message, current_context)
                return simple_response
            except Exception:
                return await self._create_fallback_response(user_message, current_context)
        except Exception as e:
            logger.error(f"Error inesperado en context builder: {e}")
            return await self._create_fallback_response(user_message, current_context)
    
    def _build_system_prompt(self) -> str:
        """Construye el prompt del sistema para GPT-3.5."""
        return """
Eres un asistente especializado en ayudar a usuarios a construir contexto para consultas complejas.

Tu rol es:
1. IDENTIFICAR si el usuario está:
   - PREGUNTANDO algo (necesita información/clarificación)
   - APORTANDO información (agregando al contexto del proyecto)

2. EXTRAER información útil de CUALQUIER mensaje (tanto preguntas como declaraciones)

3. PRESERVAR la información completa y específica del mensaje del usuario

4. GUIAR al usuario para obtener información completa y útil

5. SUGERIR FINALIZACIÓN cuando el contexto esté completo con una pregunta específica

INSTRUCCIONES CRÍTICAS PARA context_update:
- SIEMPRE extrae información útil del mensaje, incluso si es una pregunta
- Las PREGUNTAS pueden contener información valiosa: objetivos, restricciones, mercados, presupuestos, etc.
- En "context_update" incluye TODA la información relevante del mensaje actual
- PRESERVA los detalles específicos: números, fechas, ubicaciones, objetivos, restricciones
- NO resumas excesivamente - mantén la información completa y descriptiva
- NUNCA repitas información que ya está en el contexto existente
- SOLO agrega información NUEVA y DIFERENTE
- Sé específico y detallado: incluye todos los hechos importantes del usuario
- Si no hay información nueva, deja "context_update" vacío

REGLAS ESTRICTAS PARA EVITAR DUPLICACIÓN:
- Si el contexto ya menciona "startup de software dental", NO vuelvas a mencionarlo
- Si el contexto ya dice "fase beta", NO lo repitas
- SOLO agrega los elementos NUEVOS del mensaje actual
- Usa frases concisas y directas sin redundancia
- Evita repetir el tipo de empresa, industria o estado si ya están en el contexto

EJEMPLOS DE EXTRACCIÓN SIN DUPLICACIÓN:

CORRECTO - Contexto existente + mensaje nuevo:
Contexto: "Startup que ofrece software de gestión para clínicas dentales, actualmente en fase beta"
Usuario: "Estamos considerando campañas en Google Ads pero no sabemos cuánto invertir"
context_update: "Considerando campañas en Google Ads. Incertidumbre sobre cantidad de inversión publicitaria."

INCORRECTO - Con duplicación:
context_update: "Considerando campañas en Google Ads para la startup de software de gestión para clínicas dentales en fase beta"

CORRECTO - Pregunta con información valiosa:
Usuario: "¿Qué estrategia de marketing me permite alcanzar 50 clientes en México y Colombia con un CAC ≤ 150 USD y presupuesto de 2,000 USD/mes?"
message_type: "question"
context_update: "Objetivo: 50 clientes de pago. Mercados: México y Colombia. CAC máximo: 150 USD. Presupuesto mensual: 2,000 USD. Enfoque: estrategia de marketing"

CORRECTO - Declaración informativa:
Usuario: "Tengo una startup que ofrece software de gestión para clínicas dentales. Aún estamos en fase beta"
message_type: "information"
context_update: "Startup que ofrece software de gestión para clínicas dentales, actualmente en fase beta"

INSTRUCCIONES GENERALES:
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
  "context_update": "SOLO información NUEVA del mensaje actual, sin repetir lo que ya está en el contexto",
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
        """
        Actualiza el contexto acumulado con nueva información.
        Evita duplicación pero preserva información importante.
        """
        if not new_info or not new_info.strip():
            return current_context
            
        if not current_context or not current_context.strip():
            return new_info.strip()
        
        # Normalizar textos para comparación
        current_lower = current_context.lower().strip()
        new_lower = new_info.lower().strip()
        
        # Si la nueva información es idéntica o está completamente contenida, no agregar
        if new_lower == current_lower or new_lower in current_lower:
            logger.debug(f"Información duplicada detectada (contenida): {new_lower[:50]}...")
            return current_context
        
        # Verificar si hay superposición significativa de palabras (>70%)
        current_words = set(current_lower.split())
        new_words = set(new_lower.split())
        
        if len(new_words) > 0:
            overlap_ratio = len(current_words.intersection(new_words)) / len(new_words)
            
            # Si hay mucha superposición, verificar si la nueva info es más completa
            if overlap_ratio > 0.7:
                # Si la nueva información es más larga y específica, reemplazar
                if len(new_info) > len(current_context) * 1.2:
                    logger.debug(f"Reemplazando contexto con versión más completa")
                    return new_info.strip()
                # Si es similar o más corta, mantener la actual
                else:
                    logger.debug(f"Información similar detectada, manteniendo contexto actual")
                    return current_context
        
        # Detectar duplicación semántica específica
        # Verificar frases comunes que podrían estar duplicadas
        duplicate_patterns = [
            r'startup.*software.*gestión.*clínicas.*dentales',
            r'fase.*beta',
            r'software.*gestión.*clínicas.*dentales',
            r'clínicas.*dentales.*fase.*beta'
        ]
        
        import re
        for pattern in duplicate_patterns:
            # Si el patrón aparece en ambos textos, es probable duplicación
            if re.search(pattern, current_lower) and re.search(pattern, new_lower):
                # Extraer solo las partes nuevas
                logger.debug(f"Patrón duplicado detectado: {pattern}")
                
                # Intentar extraer solo información nueva
                new_parts = []
                new_sentences = new_info.split('.')
                
                for sentence in new_sentences:
                    sentence = sentence.strip()
                    if sentence and not any(re.search(pattern, sentence.lower()) for pattern in duplicate_patterns):
                        # Esta oración no contiene patrones duplicados
                        if sentence.lower() not in current_lower:
                            new_parts.append(sentence)
                
                if new_parts:
                    # Combinar solo las partes nuevas
                    new_content = '. '.join(new_parts)
                    if current_context.endswith('.'):
                        return f"{current_context} {new_content.strip()}"
                    else:
                        return f"{current_context}. {new_content.strip()}"
                else:
                    # No hay partes nuevas, mantener el contexto actual
                    logger.debug("No se encontraron partes nuevas después de filtrar duplicación")
                    return current_context
        
        # Combinar información complementaria si no hay duplicación detectada
        # Usar punto para separar información distinta
        if current_context.endswith('.'):
            return f"{current_context} {new_info.strip()}"
        else:
            return f"{current_context}. {new_info.strip()}"
    
    def include_moderator_synthesis(self, current_context: str, synthesis_text: str, key_themes: list = None, recommendations: list = None) -> str:
        """
        Incluye la síntesis del moderador en el contexto acumulado.
        
        Args:
            current_context: Contexto actual acumulado
            synthesis_text: Texto de síntesis del moderador
            key_themes: Temas clave identificados por el moderador (opcional)
            recommendations: Recomendaciones del moderador (opcional)
            
        Returns:
            Contexto actualizado con la síntesis del moderador
        """
        if not synthesis_text.strip():
            return current_context
        
        # Evitar duplicación - verificar si ya está incluida
        if "🔬 Análisis del Moderador IA" in current_context:
            logger.debug("Síntesis del moderador ya incluida en el contexto")
            return current_context
        
        # Crear resumen estructurado de la síntesis
        moderator_section = "## 🔬 Análisis del Moderador IA\n\n"
        
        # Incluir temas clave si están disponibles
        if key_themes:
            moderator_section += "**Temas Clave Identificados:**\n"
            for theme in key_themes[:3]:  # Limitar a 3 temas principales
                moderator_section += f"• {theme}\n"
            moderator_section += "\n"
        
        # Incluir recomendaciones si están disponibles
        if recommendations:
            moderator_section += "**Recomendaciones Principales:**\n"
            for rec in recommendations[:3]:  # Limitar a 3 recomendaciones principales
                moderator_section += f"• {rec}\n"
            moderator_section += "\n"
        
        # Incluir síntesis (limitada para no abrumar el contexto)
        synthesis_preview = synthesis_text[:800] + "..." if len(synthesis_text) > 800 else synthesis_text
        moderator_section += f"**Síntesis del Análisis:**\n{synthesis_preview}"
        
        # Combinar con el contexto existente
        if current_context.strip():
            return f"{current_context}\n\n{moderator_section}"
        else:
            return moderator_section
    
    def _count_context_elements(self, context: str) -> int:
        """Cuenta los elementos de contexto separados por líneas."""
        if not context.strip():
            return 0
        
        # Contar párrafos no vacíos
        elements = [line.strip() for line in context.split('\n') if line.strip()]
        return len(elements)
    
    async def _create_fallback_response(
        self, 
        user_message: str, 
        current_context: str
    ) -> ContextChatResponse:
        """Crea una respuesta de fallback en caso de error con OpenAI."""
        
        # Usar el nuevo clasificador inteligente
        message_type, confidence = await self._smart_classify(user_message)
        is_question = message_type == "question"
        
        # Si la confianza es baja, pedir aclaración
        if confidence < 0.55:
            return ContextChatResponse(
                session_id=uuid4(),
                ai_response="No estoy seguro de si eso es una pregunta o información. ¿Podrías aclararlo o aportar más detalles?",
                message_type="question",
                accumulated_context=current_context,
                suggestions=["Reformula tu mensaje", "Sé más específico", "Agrega más contexto"],
                context_elements_count=self._count_context_elements(current_context),
                suggested_final_question=None
            )
        
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
            # Si falla, usar el nuevo clasificador inteligente
            message_type, confidence = await self._smart_classify(user_message)
            is_question = message_type == "question"
            ai_response = "Entiendo. ¿Podrías contarme más detalles?" if is_question else "Perfecto, he registrado esa información."
        
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