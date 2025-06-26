import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from pydantic import BaseModel

import openai
from app.core.config import settings

# Definición de funciones disponibles para el LLM
CONTEXT_FUNCTIONS = [
    {
        "name": "summary",
        "description": "Resume el contexto actual de manera concisa",
        "parameters": {
            "type": "object",
            "properties": {
                "max_sentences": {
                    "type": "integer",
                    "description": "Número máximo de oraciones en el resumen (por defecto 2)",
                    "default": 2,
                    "minimum": 1,
                    "maximum": 5
                }
            },
            "required": []
        }
    },
    {
        "name": "show_context",
        "description": "Muestra el contexto completo actual sin modificarlo",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "clear_context",
        "description": "Borra completamente todo el contexto acumulado",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

# Modelos temporales para compatibilidad
class ContextMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime
    message_type: Optional[str] = None

class ContextChatResponse(BaseModel):
    session_id: UUID
    ai_response: str
    message_type: str
    accumulated_context: str
    suggestions: List[str]
    context_elements_count: int

class ContextSession(BaseModel):
    id: UUID
    project_id: UUID
    user_id: Optional[UUID]
    conversation_history: List[ContextMessage]
    accumulated_context: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

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

class ContextBuilderService:
    """
    Servicio para construcción conversacional de contexto usando GPT-3.5.
    
    Este servicio ayuda a los usuarios a construir contexto de manera fluida
    antes de enviar consultas a las IAs principales.
    """
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.7  # Más natural y conversacional
        self.max_tokens = 400   # Respuestas más completas para chat normal
        self.seed = None        # Sin seed para más naturalidad en conversación
    
    async def _smart_classify(self, user_message: str) -> Tuple[str, float]:
        """
        Clasifica un mensaje usando LLM multilingüe con fallback universal.
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            Tuple con (message_type, confidence)
        """
        return await classify_message_llm(self.client, user_message, self.model)
    
    def _execute_function(self, function_call, current_context: str) -> Tuple[str, str]:
        """
        Ejecuta una función solicitada por el LLM.
        
        Args:
            function_call: Objeto function_call de OpenAI
            current_context: Contexto actual
            
        Returns:
            Tuple con (result_message, updated_context)
        """
        function_name = function_call.name
        
        try:
            # Parsear argumentos si existen
            arguments = {}
            if function_call.arguments:
                arguments = json.loads(function_call.arguments)
        except json.JSONDecodeError:
            arguments = {}
        
        if function_name == "summary":
            # Resume el contexto actual
            max_sentences = arguments.get("max_sentences", 2)
            return self._create_context_summary(current_context, max_sentences), current_context
            
        elif function_name == "show_context":
            # Muestra el contexto completo
            if not current_context.strip():
                return "📋 **Contexto actual**: No hay contexto acumulado aún.", current_context
            else:
                word_count = len(current_context.split())
                char_count = len(current_context)
                return f"📋 **Contexto actual** ({word_count} palabras, {char_count} caracteres):\n\n{current_context}", current_context
                
        elif function_name == "clear_context":
            # Borra todo el contexto
            return "🗑️ **Contexto borrado**: He eliminado todo el contexto acumulado. Podemos empezar desde cero.", ""
            
        else:
            # Función desconocida
            return f"❌ **Error**: Función '{function_name}' no reconocida.", current_context
    
    def _create_context_summary(self, context: str, max_sentences: int = 2) -> str:
        """
        Crea un resumen conciso del contexto.
        
        Args:
            context: Contexto a resumir
            max_sentences: Número máximo de oraciones
            
        Returns:
            Resumen del contexto
        """
        if not context.strip():
            return "📋 **Resumen**: No hay contexto para resumir aún."
        
        # Dividir en oraciones (aproximado)
        sentences = []
        for sentence in context.replace('. ', '.\n').split('\n'):
            sentence = sentence.strip()
            if sentence and not sentence.endswith('.'):
                sentence += '.'
            if sentence and len(sentence) > 10:  # Filtrar oraciones muy cortas
                sentences.append(sentence)
        
        # Seleccionar las primeras N oraciones más importantes
        if len(sentences) <= max_sentences:
            summary = ' '.join(sentences)
        else:
            # Tomar las primeras oraciones (usualmente contienen info más importante)
            summary = ' '.join(sentences[:max_sentences])
        
        word_count = len(context.split())
        return f"📋 **Resumen del contexto** ({word_count} palabras totales):\n\n{summary}"
    
    async def _extract_information_from_message(
        self, 
        user_message: str, 
        current_context: str, 
        conversation_history: List[ContextMessage] = None
    ) -> str:
        """
        Extrae información específica de un mensaje del usuario usando el contexto conversacional.
        
        Args:
            user_message: Mensaje del usuario
            current_context: Contexto actual para evitar duplicación
            conversation_history: Historial reciente de la conversación
            
        Returns:
            Información extraída del mensaje con contexto conversacional
        """
        
        if conversation_history is None:
            conversation_history = []
        # Llamada simple a GPT para extraer información específica
        try:
            # Construir historial conversacional reciente para contexto
            recent_conversation = ""
            if conversation_history:
                recent_messages = conversation_history[-4:]  # Últimos 4 mensajes para contexto
                for i, msg in enumerate(recent_messages):
                    role_emoji = "👤" if msg.role == "user" else "🤖"
                    recent_conversation += f"{role_emoji} {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}\n"
            
            prompt = f"""
            Extrae toda la información relevante de este mensaje del usuario, usando el contexto de la conversación para entender mejor las referencias:

            MENSAJE ACTUAL: "{user_message}"

            CONTEXTO CONVERSACIONAL RECIENTE:
            {recent_conversation if recent_conversation.strip() else "No hay conversación previa"}

            CONTEXTO ACUMULADO DEL PROYECTO:
            {current_context if current_context.strip() else "No hay contexto previo"}

            INSTRUCCIONES:
            - Usa el contexto conversacional para entender referencias como "opción 2", "eso", "lo anterior", etc.
            - Extrae información específica y contextual (ej: "Decisión: Opción 2 para construir startup de envases de banana")
            - Incluye información sobre decisiones, preferencias, números específicos, ubicaciones, restricciones
            - Evita repetir exactamente lo que ya está en el contexto acumulado
            - Si el mensaje es solo una referencia sin contexto conversacional, extrae lo que puedas
            - Sé específico y útil para futuras consultas
            - Si no hay información nueva, responde ""

            INFORMACIÓN EXTRAÍDA:
            """
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            extracted = response.choices[0].message.content.strip()
            return extracted if extracted and extracted != '""' else ""
            
        except Exception as e:
            logger.debug(f"Error extrayendo información: {e}")
            # Fallback: extraer información básica usando heurísticas
            return self._extract_info_heuristic(user_message, current_context, conversation_history)
    
    def _extract_info_heuristic(
        self, 
        user_message: str, 
        current_context: str,
        conversation_history: List[ContextMessage] = None
    ) -> str:
        """
        Extrae información usando heurísticas simples como fallback.
        
        Args:
            user_message: Mensaje del usuario
            current_context: Contexto actual
            conversation_history: Historial de conversación
            
        Returns:
            Información extraída usando heurísticas
        """
        
        if conversation_history is None:
            conversation_history = []
        info_parts = []
        message_lower = user_message.lower()
        
        # Detectar referencias contextuales
        if any(ref in message_lower for ref in ['opción', 'option', 'me quedo', 'elijo', 'prefiero']):
            # Buscar en el historial qué opciones se mencionaron
            for msg in reversed(conversation_history[-6:]):  # Últimos 6 mensajes
                if msg.role == "assistant" and any(word in msg.content.lower() for word in ['opción', 'option', '1.', '2.', '3.']):
                    # Intentar extraer el contexto del proyecto del historial
                    project_context = ""
                    for hist_msg in conversation_history:
                        if any(term in hist_msg.content.lower() for term in ['startup', 'empresa', 'negocio', 'envases', 'banana']):
                            project_context = hist_msg.content[:50] + "..."
                            break
                    
                    if "opción 2" in message_lower or "option 2" in message_lower:
                        info_parts.append(f"Decisión: Opción 2 seleccionada {f'(relacionado con {project_context})' if project_context else ''}")
                    elif "opción" in message_lower or "option" in message_lower:
                        info_parts.append(f"Decisión de opción tomada {f'(relacionado con {project_context})' if project_context else ''}")
                    break
        
        # Buscar números importantes (presupuestos, objetivos, etc.)
        import re
        numbers = re.findall(r'\b\d+[,.]?\d*\b', user_message)
        if numbers:
            info_parts.append(f"Números mencionados: {', '.join(numbers)}")
        
        # Buscar palabras clave de información
        keywords = ['startup', 'empresa', 'negocio', 'producto', 'servicio', 'cliente', 'usuario', 'mercado', 'presupuesto']
        for keyword in keywords:
            if keyword in message_lower and keyword not in current_context.lower():
                # Extraer contexto alrededor de la palabra clave
                words = user_message.split()
                for i, word in enumerate(words):
                    if keyword in word.lower():
                        start = max(0, i-2)
                        end = min(len(words), i+3)
                        context_snippet = ' '.join(words[start:end])
                        info_parts.append(context_snippet)
                        break
        
        return '. '.join(info_parts) if info_parts else ""
    
    def _generate_contextual_suggestions(self, message_type: str, context: str) -> List[str]:
        """
        Genera sugerencias contextuales basadas en el tipo de mensaje y contexto.
        
        Args:
            message_type: Tipo de mensaje (question/information)
            context: Contexto actual
            
        Returns:
            Lista de sugerencias relevantes
        """
        if message_type == "question":
            return [
                "Comparte más detalles sobre tu situación",
                "Describe tu proyecto o empresa",
                "Menciona tus objetivos específicos"
            ]
        else:  # information
            context_length = len(context.split()) if context.strip() else 0
            
            if context_length < 20:
                return [
                    "Agrega más información sobre tu proyecto",
                    "Describe tus principales desafíos", 
                    "Comparte tus objetivos y restricciones"
                ]
            elif context_length < 50:
                return [
                    "¿Hay algo más relevante que agregar?",
                    "Describe tu situación actual",
                    "Menciona cualquier restricción importante"
                ]
            else:
                return [
                    "El contexto está bastante completo",
                    "Puedes hacer preguntas específicas ahora",
                    "¿Necesitas resumir lo que hemos discutido?"
                ]
    
    async def process_user_message(
        self,
        user_message: str,
        conversation_history: List[ContextMessage],
        current_context: str
    ) -> ContextChatResponse:
        """
        Procesa un mensaje del usuario usando function calling.
        
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
            
            # Si la confianza es baja, pedir aclaración
            if confidence < 0.55:
                return ContextChatResponse(
                    session_id=uuid4(),
                    ai_response="No estoy seguro de si eso es una pregunta o información. ¿Podrías aclararlo o aportar más detalles?",
                    message_type="question",
                    accumulated_context=current_context,
                    suggestions=["Reformula tu mensaje", "Sé más específico", "Agrega más contexto"],
                    context_elements_count=self._count_context_elements(current_context)
                )
            
            # Construir mensajes para GPT-3.5
            system_prompt = self._build_system_prompt()
            messages = self._build_conversation_messages(
                system_prompt, user_message, conversation_history, current_context
            )
            
            # Llamar a GPT-3.5 con function calling
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                functions=CONTEXT_FUNCTIONS,
                function_call="auto",
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                seed=self.seed
            )
            
            # Procesar respuesta
            choice = response.choices[0]
            updated_context = current_context
            
            # Verificar si hay function_call
            if choice.message.function_call:
                # Ejecutar función solicitada
                function_result, updated_context = self._execute_function(choice.message.function_call, current_context)
                
                return ContextChatResponse(
                    session_id=uuid4(),
                    ai_response=function_result,
                    message_type="command_result",
                    accumulated_context=updated_context,
                    suggestions=["Continúa compartiendo información", "Haz más preguntas"],
                    context_elements_count=self._count_context_elements(updated_context)
                )
            else:
                # Respuesta normal sin function call
                ai_response = choice.message.content or "¿Podrías darme más detalles?"
                
                # Si es información, extraer datos específicos del mensaje
                if message_type == "information":
                    extracted_info = await self._extract_information_from_message(
                        user_message, current_context, conversation_history
                    )
                    if extracted_info.strip():
                        updated_context = self._update_accumulated_context(current_context, extracted_info)
                
                # Generar sugerencias contextuales
                suggestions = self._generate_contextual_suggestions(message_type, updated_context)
                
                return ContextChatResponse(
                    session_id=uuid4(),
                    ai_response=ai_response,
                    message_type=message_type,
                    accumulated_context=updated_context,
                    suggestions=suggestions,
                    context_elements_count=self._count_context_elements(updated_context)
                )
            
        except openai.APIError as e:
            logger.error(f"Error de API de OpenAI: {e}")
            return await self._create_fallback_response(user_message, current_context, conversation_history)
        except openai.RateLimitError as e:
            logger.error(f"Rate limit excedido en OpenAI: {e}")
            return await self._create_fallback_response(user_message, current_context, conversation_history)
        except Exception as e:
            logger.error(f"Error inesperado en context builder: {e}")
            return await self._create_fallback_response(user_message, current_context, conversation_history)
    
    def _build_system_prompt(self) -> str:
        """Construye el prompt del sistema para un chat conversacional completo."""
        return """Eres un asistente conversacional inteligente y completo que puede:

1. **RESPONDER CUALQUIER PREGUNTA** usando tu conocimiento general:
   - Preguntas sobre cualquier tema: "¿cuáles son los países más exportadores de banana?"
   - Explicaciones de conceptos: "¿qué es machine learning?"
   - Consejos generales: "¿cómo mejorar mi productividad?"
   - Cálculos y análisis: "¿cuánto es 15% de 850?"

2. **MANTENER CONVERSACIONES NATURALES** sobre cualquier tema de interés del usuario

3. **RECONOCER INFORMACIÓN RELEVANTE** cuando el usuario comparte detalles de su proyecto/negocio:
   - Números específicos, objetivos, restricciones
   - Datos sobre su empresa, producto, o situación
   - Información que podría ser útil para consultas especializadas

4. **CONSTRUIR CONTEXTO GRADUALMENTE** para cuando el usuario quiera consultar IAs especializadas

**COMPORTAMIENTO:**
- Responde de manera natural y útil a CUALQUIER pregunta
- Si detectas información relevante del proyecto del usuario, reconócela sutilmente
- Mantén un tono amigable, profesional y conversacional
- No te limites solo a "construcción de contexto" - eres un chat completo

**FUNCIONES DISPONIBLES:**
- summary(): Resume el contexto actual del proyecto
- show_context(): Muestra contexto completo del proyecto  
- clear_context(): Borra contexto del proyecto

Actúa como un asistente conversacional normal que ADEMÁS tiene la capacidad especial de construir contexto cuando es relevante."""
    
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
        logger.info(f"🔍 Context Builder recibe {len(conversation_history)} mensajes totales, usando últimos {len(recent_history)}")
        
        for i, msg in enumerate(recent_history):
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
            logger.info(f"  📋 Msg {i+1}: {msg.role} -> {msg.content[:50]}...")
        
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
        
        # Solo evitar duplicación exacta
        if new_lower == current_lower:
            logger.debug(f"Información exactamente duplicada detectada")
            return current_context
        
        # Si la nueva información está completamente contenida (pero no es exacta), agregar igual
        # para que se mantenga la información completa
        if new_lower in current_lower and len(new_lower) < len(current_lower) * 0.8:
            logger.debug(f"Información ya contenida en contexto existente")
            return current_context
        
        # Si la nueva información es mucho más completa que la actual, reemplazar
        if len(new_info) > len(current_context) * 1.5:
            logger.debug(f"Reemplazando contexto con versión mucho más completa")
            return new_info.strip()
        
        # En todos los demás casos, combinar la información
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
        current_context: str,
        conversation_history: List[ContextMessage] = None
    ) -> ContextChatResponse:
        """Crea una respuesta de fallback en caso de error con OpenAI."""
        
        if conversation_history is None:
            conversation_history = []
        
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
                context_elements_count=self._count_context_elements(current_context)
            )
        
        if is_question:
            # Es una pregunta - usar historial para generar respuesta contextual
            updated_context = current_context
            
            if len(conversation_history) == 0:
                # Primera interacción
                response_text = "¡Hola! Estoy aquí para ayudarte a construir el contexto de tu consulta. ¿Podrías contarme más sobre tu proyecto o situación?"
                suggestions = [
                    "Describe tu proyecto o empresa",
                    "Comparte los principales desafíos",
                    "Explica qué tipo de ayuda necesitas"
                ]
            else:
                # Hay historial previo - intentar dar respuesta contextual básica
                logger.info(f"🔄 Fallback con historial: {len(conversation_history)} mensajes")
                
                # Generar respuesta básica basada en el contexto
                if "capital" in user_message.lower() and len(conversation_history) >= 2:
                    # Pregunta sobre capital después de hablar de países
                    last_assistant_msg = None
                    for msg in reversed(conversation_history):
                        if msg.role == "assistant":
                            last_assistant_msg = msg.content
                            break
                    
                    if last_assistant_msg and ("ecuador" in last_assistant_msg.lower() or "banana" in last_assistant_msg.lower()):
                        response_text = "La capital de Ecuador es Quito. ¿Te gustaría saber algo más sobre Ecuador o tienes alguna otra pregunta?"
                    else:
                        response_text = "Perdón, necesito más contexto. ¿De qué país te refieres la capital?"
                else:
                    # Respuesta genérica pero conversacional
                    response_text = "Perdón, tuve un problema técnico. ¿Podrías reformular tu pregunta o darme más detalles?"
                
                suggestions = [
                    "Reformula tu pregunta",
                    "Agrega más contexto",
                    "Haz una pregunta más específica"
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
        
        # El chat es infinito - no hay finalización automática
        suggested_question = None
        
        return ContextChatResponse(
            session_id=uuid4(),
            ai_response=response_text,
            message_type=message_type,
            accumulated_context=updated_context,
            suggestions=suggestions,
            context_elements_count=context_elements
        )
    

    

    

    


# Instancia global del servicio
context_builder_service = ContextBuilderService() 