import json
import openai
from typing import Dict, Any
from app.models.pre_analysis import PreAnalysisResult
from app.core.config import settings

# Sistema prompt para el análisis de intenciones
SYSTEM_PROMPT = """Eres un asistente experto que ayuda a interpretar preguntas de usuarios sobre investigación, ideas o planificación. Tu tarea es:

1. Analizar la intención principal del usuario.
2. Identificar si hay datos faltantes o ambigüedades en la pregunta.
3. Proponer una pregunta mejorada solo si la información es suficiente.

Responde siempre en JSON válido con los siguientes campos:
- interpreted_intent: string (explica brevemente lo que el usuario quiere)
- clarification_questions: lista de strings (preguntas que ayudarían a mejorar la comprensión)
- refined_prompt_candidate: string o null (versión mejorada de la pregunta si está todo claro)

Si hay información suficiente para generar una respuesta útil, deja clarification_questions vacío y proporciona refined_prompt_candidate.
Si faltan datos importantes, genera 2-4 preguntas específicas y deja refined_prompt_candidate como null."""

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
            return PreAnalysisResult(
                interpreted_intent=parsed_result.get("interpreted_intent", ""),
                clarification_questions=parsed_result.get("clarification_questions", []),
                refined_prompt_candidate=parsed_result.get("refined_prompt_candidate")
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