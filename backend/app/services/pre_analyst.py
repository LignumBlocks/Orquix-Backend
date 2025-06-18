import json
import openai
from typing import Dict, Any
from app.models.pre_analysis import PreAnalysisResult
from app.core.config import settings

# Sistema prompt para el análisis de intenciones
SYSTEM_PROMPT = """Eres un asistente experto que ayuda a interpretar preguntas de usuarios sobre investigación, ideas o planificación. Tu tarea es:

1. Analizar la intención principal del usuario.
2. Identificar si hay datos faltantes o ambigüedades en la pregunta.
3. SIEMPRE proponer una versión mejorada de la pregunta, incluso si falta información.

Reglas importantes:
1. Para preguntas vagas o muy generales, SIEMPRE genera 2-4 preguntas de clarificación.
2. refined_prompt_candidate NUNCA debe ser null o vacío.
3. Si la pregunta es específica y clara, deja clarification_questions vacío.
4. Si hay ambigüedad, genera preguntas que ayuden a entender:
   - Contexto específico que le interesa al usuario
   - Aspectos particulares que quiere explorar
   - Perspectiva o enfoque deseado
   - Nivel de detalle requerido

Responde siempre en JSON válido con los siguientes campos:
- interpreted_intent: string (explica brevemente lo que el usuario quiere)
- clarification_questions: lista de strings (preguntas que ayudarían a mejorar la comprensión, máximo 4)
- refined_prompt_candidate: string (SIEMPRE presente - versión mejorada de la pregunta usando la información disponible)

Ejemplos:

1. Input vago: "¿qué opinas sobre la automatización?"
   {
     "interpreted_intent": "El usuario quiere conocer perspectivas sobre el impacto de la automatización",
     "clarification_questions": [
       "¿Te interesa algún sector específico (industria, servicios, etc.)?",
       "¿Quieres enfocarte en impactos económicos, sociales o tecnológicos?",
       "¿Buscas información sobre tendencias actuales o proyecciones futuras?",
       "¿Te preocupa algún aspecto particular (empleo, productividad, etc.)?"
     ],
     "refined_prompt_candidate": "Analiza los principales impactos y tendencias de la automatización, considerando sus beneficios y desafíos en diferentes sectores"
   }

2. Input específico: "Explica el impacto de la automatización en call centers de Latinoamérica"
   {
     "interpreted_intent": "El usuario quiere entender cómo la automatización afecta específicamente a los call centers en Latinoamérica",
     "clarification_questions": [],
     "refined_prompt_candidate": "Analiza el impacto actual y proyectado de la automatización en los call centers latinoamericanos, incluyendo efectos en empleo, productividad y calidad de servicio"
   }"""

class PreAnalystService:
    """Servicio para análisis previo de prompts del usuario."""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo-1106"
        self.temperature = 0.3
    
    async def analyze_prompt(self, user_prompt_text: str) -> PreAnalysisResult:
        """
        Analiza un prompt del usuario para interpretar su intención,
        identificar información faltante y generar preguntas de clarificación.
        
        Args:
            user_prompt_text: El texto del prompt del usuario
            
        Returns:
            PreAnalysisResult con la interpretación y preguntas de clarificación
            
        Raises:
            Exception: Si hay error en la llamada a OpenAI o parsing del JSON
        """
        try:
            # Llamada a OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt_text}
                ]
            )
            
            # Extraer contenido de la respuesta
            content = response.choices[0].message.content.strip()
            
            # Parsear JSON
            parsed_result = json.loads(content)
            
            # Validar y crear resultado
            refined_candidate = parsed_result.get("refined_prompt_candidate", "").strip()
            if not refined_candidate:
                # Fallback: usar el prompt original si no hay refined_candidate
                refined_candidate = user_prompt_text
            
            return PreAnalysisResult(
                interpreted_intent=parsed_result.get("interpreted_intent", ""),
                clarification_questions=parsed_result.get("clarification_questions", []),
                refined_prompt_candidate=refined_candidate
            )
            
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing JSON response from OpenAI: {str(e)}")
        except openai.OpenAIError as e:
            raise Exception(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error in PreAnalyst service: {str(e)}")
    
    def is_prompt_complete(self, analysis_result: PreAnalysisResult) -> bool:
        """
        Determina si un prompt está completo basado en el resultado del análisis.
        
        Args:
            analysis_result: Resultado del análisis previo
            
        Returns:
            True si el prompt está completo (tiene refined_prompt_candidate)
        """
        return (
            analysis_result.refined_prompt_candidate is not None and 
            len(analysis_result.clarification_questions) == 0
        )

# Instancia global del servicio
pre_analyst_service = PreAnalystService() 