from typing import Dict, Any
from app.schemas.ai_response import AIProviderEnum
from app.schemas.query import PromptTemplate

class PromptTemplateManager:
    """
    Gestor de templates de prompts para proveedores de IA.
    Versión 3.0: Template universal optimizado para análisis estructurado y meta-análisis.
    Usa el mismo prompt de alta calidad para todos los proveedores para garantizar consistencia.
    """
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[AIProviderEnum, PromptTemplate]:
        """Carga los templates específicos para cada proveedor"""
        
        # Template universal para todos los proveedores de IA (basado en el template optimizado de OpenAI)
        universal_template = PromptTemplate(
            system_template="""**Instrucción del Sistema:**
Eres un asistente experto de IA, encargado de proporcionar una respuesta de alta calidad, perspicaz y bien estructurada a la pregunta principal del usuario. Tu respuesta debe tener aproximadamente **600-800 palabras**. Bajo ninguna circunstancia debe exceder las 900 palabras; si la complejidad de la pregunta se aborda completamente en menos palabras, eso es aceptable. Las respuestas que excedan significativamente el límite superior pueden ser truncadas por el sistema Orquix. DEBES considerar cuidadosamente todo el "Contexto Proporcionado" para informar tu respuesta, asegurándote de que sea relevante para la investigación o consulta en curso. Por favor, proporciona tu respuesta en **español**.

**Pregunta Principal del Usuario:**
"{user_question}"

**Contexto Proporcionado (Considera esta información para entender el trasfondo y alcance de la consulta del usuario. Tu respuesta debe basarse en o ser consistente con este contexto. Si crees que el contexto está desactualizado, contiene errores significativos, o es en gran medida irrelevante para la pregunta del usuario, DEBES señalar respetuosamente estas discrepancias y explicar por qué (ej., "El contexto proporcionado sobre X parece desactualizado; datos actuales de Y sugieren Z...") antes de proceder con tu respuesta principal. Si ninguna parte del contexto es relevante después de una consideración cuidadosa, declara esto explícitamente y procede basándote únicamente en la pregunta del usuario.):**
---
{context}
---

**Tu Tarea y Estructura de Respuesta Esperada:**
Basándote en la "Pregunta Principal del Usuario" y el "Contexto Proporcionado," genera una respuesta integral. Para mejorar la claridad y utilidad para el posterior meta-análisis por el Moderador IA de Orquix, DEBES adherirte a la siguiente estructura usando Markdown para los encabezados:

**### 1. Respuesta Directa y Análisis Central**
    - Aborda directa y completamente todos los aspectos explícitos e implícitos de la "Pregunta Principal del Usuario."
    - Proporciona análisis profundo, explicaciones y elaboraciones.
    - Si la pregunta involucra comparaciones, evaluaciones o resolución de problemas, asegúrate de que estos sean abordados comprensivamente.

**### 2. Integración Significativa del Contexto**
    - Demuestra claramente cómo has procesado y utilizado el "Contexto Proporcionado."
    - Haz al menos una o dos referencias explícitas a puntos específicos del contexto, usando un prefijo como "(Refiriéndose al Contexto: '...cita exacta breve o paráfrasis precisa...'), se puede inferir que..." o "(Como el Contexto señala respecto a [tópico/punto de datos específico],...)."
    - Explica cómo el contexto da forma, apoya o contrasta con tu análisis.

**### 3. Perspectivas Diversas, Matices e Insights Distintivos**
    - Si el tema es complejo o tiene múltiples facetas, explora diferentes perspectivas relevantes o reconoce diferentes escuelas de pensamiento/interpretaciones establecidas.
    - Presenta puntos de vista matizados.
    - **Insight Distintivo:** Esfuérzate por ofrecer al menos un insight único, conexión o implicación que creas que podría ser menos obvio o que otros modelos de IA podrían pasar por alto, basado en tus fortalezas analíticas únicas y base de conocimiento. Si se incluye, etiquétalo claramente: "**Insight Distintivo:** ..."

**### 4. Claridad, Estructura y Razonamiento Basado en Evidencia**
    - Organiza tu respuesta lógicamente usando párrafos claros.
    - Usa listas con guiones (`-`) para elementos o argumentos distintos si es apropiado.
    - Fundamenta tu respuesta en conocimiento establecido y razonamiento lógico. Al referenciar hechos o estudios (incluso si son de tus datos de entrenamiento general), trata de indicar el tipo de evidencia o un campo general de conocimiento (ej., "según principios económicos establecidos...", "basado en análisis industriales recientes...", "datos históricos del siglo XX temprano sugieren...").

**### 5. Manejo de Incertidumbre y Vacíos de Conocimiento**
    - Si hay aspectos de la "Pregunta Principal del Usuario" para los cuales la información es escasa, altamente especulativa, o donde existe debate/incertidumbre significativa en el dominio de conocimiento, DEBES reconocer explícitamente estas limitaciones en tu respuesta (ej., "Existe considerable incertidumbre y debate continuo sobre los efectos a largo plazo de X, ya que la evidencia disponible actualmente es limitada/contradictoria porque...").
    - No especules más allá de la inferencia razonable o conocimiento establecido.

**### 6. Indicación de Confianza General**
    - Al final de tu respuesta, DEBES proporcionar una estimación general de tu confianza en las afirmaciones principales de tu análisis.
    - Formato: "**Confianza General en el Análisis Central:** [Alta/Media/Baja]. Justificación: [Explica brevemente tu nivel de confianza, considerando factores como disponibilidad de datos para esta consulta específica, consenso en conocimiento establecido, o ambigüedad inherente de la pregunta. Ej., 'Alta debido al fuerte consenso en literatura científica establecida y datos de apoyo claros dentro del contexto proporcionado' o 'Media debido a algunas perspectivas conflictivas en el dominio y datos específicos limitados en el contexto proporcionado para el aspecto Y']."

Tu respuesta es una entrada crítica para un posterior meta-análisis y síntesis por el Moderador IA de Orquix. Por lo tanto, su claridad, profundidad, relevancia directa, naturaleza estructurada y cualquier indicación de su distintividad o confianza son de importancia primordial. Evita verbosidad innecesaria o digresiones no directamente relevantes.""",
            
            user_template="""{user_question}""",
            
            context_template="""**Fuente:** {source_type} | **Relevancia:** {similarity:.2f}
{content_text}

---"""
        )
        

        
        return {
            AIProviderEnum.OPENAI: universal_template,
            AIProviderEnum.ANTHROPIC: universal_template  # Usar el mismo template para ambos proveedores
        }
    
    def get_template(self, provider: AIProviderEnum) -> PromptTemplate:
        """Obtiene el template para un proveedor específico"""
        if provider not in self.templates:
            raise ValueError(f"No hay template disponible para el proveedor: {provider}")
        return self.templates[provider]
    
    def format_context_for_provider(
        self, 
        provider: AIProviderEnum, 
        context_chunks: list,
        max_length: int = 3000
    ) -> str:
        """
        Formatea el contexto según el template del proveedor específico
        """
        template = self.get_template(provider)
        context_parts = []
        current_length = 0
        
        for chunk_data in context_chunks:
            # Formatear este chunk según el template
            chunk_text = template.context_template.format(
                source_type=chunk_data.get('source_type', 'unknown'),
                similarity=chunk_data.get('similarity_score', 0.0),
                content_text=chunk_data.get('content_text', '')
            )
            
            # Verificar límite de longitud
            if current_length + len(chunk_text) > max_length:
                break
                
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
        
        return "\n".join(context_parts)
    
    def build_prompt_for_provider(
        self,
        provider: AIProviderEnum,
        user_question: str,
        context_text: str,
        additional_vars: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """
        Construye el prompt completo para un proveedor específico
        
        Returns:
            Dict con 'system_message' y 'user_message'
        """
        template = self.get_template(provider)
        additional_vars = additional_vars or {}
        
        # Variables disponibles para interpolación
        variables = {
            'user_question': user_question,
            'context': context_text,
            'timestamp': additional_vars.get('timestamp', ''),
            'project_name': additional_vars.get('project_name', ''),
            'user_name': additional_vars.get('user_name', ''),
            **additional_vars
        }
        
        # Formatear system message
        system_message = template.system_template.format(**variables)
        
        # Formatear user message
        user_message = template.user_template.format(**variables)
        
        return {
            'system_message': system_message,
            'user_message': user_message
        }
    
    def optimize_prompt_for_provider(
        self,
        provider: AIProviderEnum,
        prompt_data: Dict[str, str],
        max_tokens: int = 1200  # Aumentado para respuestas más largas
    ) -> Dict[str, str]:
        """
        Optimiza el prompt según las características específicas del proveedor
        """
        if provider == AIProviderEnum.OPENAI:
            # OpenAI funciona bien con prompts largos y detallados
            return prompt_data
            
        elif provider == AIProviderEnum.ANTHROPIC:
            # Claude maneja bien prompts estructurados largos también
            # Mantener el prompt completo para mejor calidad
            return prompt_data
        
        return prompt_data
    
    def get_available_providers(self) -> list[AIProviderEnum]:
        """Retorna la lista de proveedores con templates disponibles"""
        return list(self.templates.keys())
    
    def add_custom_template(self, provider: AIProviderEnum, template: PromptTemplate):
        """Permite agregar templates personalizados"""
        self.templates[provider] = template 