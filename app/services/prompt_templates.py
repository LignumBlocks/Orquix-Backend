from typing import Dict, Any
from app.schemas.ai_response import AIProviderEnum
from app.schemas.query import PromptTemplate

class PromptTemplateManager:
    """
    Gestor de templates de prompts específicos para cada proveedor de IA.
    Cada IA tiene su formato óptimo para recibir contexto y preguntas.
    """
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[AIProviderEnum, PromptTemplate]:
        """Carga los templates específicos para cada proveedor"""
        
        # Template para OpenAI (GPT-4o-mini)
        openai_template = PromptTemplate(
            system_template="""Eres un asistente de IA especializado en responder preguntas basándote en contexto específico.

INSTRUCCIONES:
- Usa ÚNICAMENTE la información proporcionada en el contexto para responder
- Si la información no está en el contexto, indica claramente que no tienes esa información
- Sé preciso y conciso en tu respuesta
- Si hay múltiples fuentes de información, menciona las más relevantes
- Responde en español

CONTEXTO DISPONIBLE:
{context}

---""",
            
            user_template="""{user_question}""",
            
            context_template="""**Fuente:** {source_type} | **Relevancia:** {similarity:.2f}
{content_text}

---"""
        )
        
        # Template para Anthropic Claude
        anthropic_template = PromptTemplate(
            system_template="""Eres Claude, un asistente de IA creado por Anthropic. Tu tarea es responder preguntas basándote estrictamente en el contexto proporcionado.

Reglas importantes:
1. SOLO usa información del contexto proporcionado
2. Si no hay información suficiente en el contexto, di explícitamente que no puedes responder con la información disponible
3. Cita las fuentes cuando sea relevante
4. Mantén un tono profesional y útil
5. Responde en español

Contexto disponible:
{context}""",
            
            user_template="""Pregunta: {user_question}

Por favor, responde basándote únicamente en el contexto proporcionado arriba.""",
            
            context_template="""[Fuente: {source_type} - Relevancia: {similarity:.1%}]
{content_text}

"""
        )
        
        return {
            AIProviderEnum.OPENAI: openai_template,
            AIProviderEnum.ANTHROPIC: anthropic_template
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
        max_tokens: int = 1000
    ) -> Dict[str, str]:
        """
        Optimiza el prompt según las características específicas del proveedor
        """
        if provider == AIProviderEnum.OPENAI:
            # OpenAI funciona bien con prompts largos y detallados
            return prompt_data
            
        elif provider == AIProviderEnum.ANTHROPIC:
            # Claude prefiere prompts más concisos y estructurados
            # Podríamos acortar el system message si es muy largo
            system_msg = prompt_data['system_message']
            if len(system_msg) > 2000:  # Si es muy largo
                # Versión más concisa para Claude
                system_msg = """Responde la pregunta basándote únicamente en el contexto proporcionado. Si no hay información suficiente, indícalo claramente.

""" + prompt_data.get('context', '')
                
                return {
                    'system_message': system_msg,
                    'user_message': prompt_data['user_message']
                }
        
        return prompt_data
    
    def get_available_providers(self) -> list[AIProviderEnum]:
        """Retorna la lista de proveedores con templates disponibles"""
        return list(self.templates.keys())
    
    def add_custom_template(self, provider: AIProviderEnum, template: PromptTemplate):
        """Permite agregar templates personalizados"""
        self.templates[provider] = template 