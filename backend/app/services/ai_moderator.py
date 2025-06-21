from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from app.schemas.ai_response import StandardAIResponse, AIResponseStatus, AIRequest, AIProviderEnum
from app.services.ai_adapters.openai_adapter import OpenAIAdapter
from app.services.ai_adapters.anthropic_adapter import AnthropicAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)

class SynthesisQuality(str, Enum):
    """Calidad de la síntesis generada"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FAILED = "failed"

class ModeratorResponse(BaseModel):
    """Respuesta del moderador con síntesis y metadatos v2.0"""
    synthesis_text: str
    quality: SynthesisQuality
    key_themes: List[str]
    contradictions: List[str]
    consensus_areas: List[str]
    source_references: Dict[str, List[str]]  # provider -> list of points
    
    # Nuevos campos v2.0 para meta-análisis profesional
    recommendations: List[str] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
    research_areas: List[str] = Field(default_factory=list)
    connections: List[str] = Field(default_factory=list)
    meta_analysis_quality: str = "unknown"  # complete, partial, incomplete, error
    
    # Metadatos existentes
    processing_time_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    fallback_used: bool = False
    original_responses_count: int = 0
    successful_responses_count: int = 0

class AIModerator:
    """
    Moderador IA que sintetiza respuestas de múltiples proveedores.
    Implementa síntesis extractiva mejorada usando LLM económico.
    """
    
    def __init__(self):
        self.synthesis_adapter = None
        self._initialize_synthesis_adapter()
    
    def _initialize_synthesis_adapter(self):
        """Inicializa el adaptador para síntesis (LLM económico)"""
        try:
            # Priorizar Claude 3 Haiku por ser más económico
            if settings.ANTHROPIC_API_KEY:
                self.synthesis_adapter = AnthropicAdapter(
                    api_key=settings.ANTHROPIC_API_KEY,
                    model="claude-3-haiku-20240307"
                )
                logger.info("Moderador inicializado con Claude 3 Haiku")
                return
        except Exception as e:
            logger.warning(f"Error inicializando Claude para síntesis: {e}")
        
        try:
            # Fallback a GPT-3.5-Turbo
            if settings.OPENAI_API_KEY:
                self.synthesis_adapter = OpenAIAdapter(
                    api_key=settings.OPENAI_API_KEY,
                    model="gpt-3.5-turbo"
                )
                logger.info("Moderador inicializado con GPT-3.5-Turbo")
                return
        except Exception as e:
            logger.warning(f"Error inicializando GPT-3.5 para síntesis: {e}")
        
        logger.error("No se pudo inicializar ningún adaptador para síntesis")
    
    def _create_synthesis_prompt(self, responses: List[StandardAIResponse]) -> str:
        """Crea el prompt v2.0 de meta-análisis profesional para síntesis avanzada"""
        
        # Filtrar solo respuestas exitosas
        successful_responses = [
            r for r in responses 
            if r.status == AIResponseStatus.SUCCESS and r.response_text
        ]
        
        if not successful_responses:
            return ""
        
        # Construir las respuestas en el formato requerido
        external_ai_responses = ""
        for i, response in enumerate(successful_responses, 1):
            provider_name = response.ia_provider_name.value.upper()
            external_ai_responses += f"[AI_Modelo_{provider_name}] dice: {response.response_text.strip()}\n\n"
        
        # Crear el prompt v2.0 completo
        prompt = f"""**System Role:**
Eres un asistente de meta-análisis objetivo, analítico y altamente meticuloso. Tu tarea principal es procesar un conjunto de respuestas de múltiples modelos de IA diversos (`external_ai_responses`) a una consulta específica del investigador (`user_question`). Tu objetivo es generar un reporte estructurado, claro y altamente accionable (objetivo total de salida: aproximadamente 800-1000 tokens) que ayude al investigador a:
    a) Comprender las perspectivas diversas y contribuciones clave de cada IA.
    b) Identificar puntos cruciales de consenso y contradicciones factuales obvias.
    c) Reconocer cobertura temática, énfasis y omisiones notables.
    d) Definir pasos lógicos y accionables para su investigación o consulta.

Prioriza precisión, relevancia directa a la `user_question`, y claridad en todos los componentes de tu salida. **Si encuentras incertidumbre significativa o si los datos de entrada son insuficientes para un análisis robusto de una sección particular, DEBES declarar explícitamente esta limitación** (ej., "- Datos insuficientes o alta divergencia en respuestas de IA impide una evaluación confiable para esta sección.") en lugar de forzar una declaración especulativa o de baja calidad. Adhiérete estrictamente a las instrucciones "si no... declara..." proporcionadas para secciones específicas. Asegúrate de que todo el reporte sea generado en **español**.

**Contexto de Entrada que Recibirás:**
1. `user_question`: La pregunta original planteada por el investigador.
2. `external_ai_responses`: Un conjunto de respuestas textuales, cada una identificada por su IA fuente.

**Tu Tarea Principal:**
Analiza la `user_question` y las `external_ai_responses` para generar un reporte estructurado con los siguientes componentes, usando Markdown para encabezados (ej., `## 1. Evaluación Inicial...`, `### 2.a. ...`) y listas con guiones (`-`) para elementos. Usa Markdown en negrita (`**texto**`) para resaltar **solo una única pieza de información o recomendación más crítica** dentro de cada una de las subsecciones numeradas principales (0, 1, 2.b, 2.c, 2.d, 3.a, 3.b, 3.c) si, y solo si, una se destaca claramente como primordial para la atención inmediata del usuario. Si ningún punto es significativamente más crítico que otros en una subsección, no uses resaltado en negrita en esa subsección.

**0. Evaluación Inicial de Relevancia de Entradas (Si Aplica):**
    - (Si alguna de las `external_ai_responses` está claramente fuera de tema, es ininteligible, o falla en abordar la `user_question` sustancialmente, nota esto brevemente al principio. Ejemplo: "- La respuesta de `[AI_Modelo_X]` parece ser mayormente irrelevante para la pregunta formulada y se ha ponderado menos en el análisis comparativo." Si todas son pertinentes, omite esta sección.)

**## 1. Resumen Conciso General y Recomendación Clave**
    - Un párrafo muy breve (2-3 frases, **máximo 50 palabras**) capturando la idea o conclusión principal del conjunto de respuestas, SOLO si emerge un tema central fuerte y unificador a través de la mayoría de las respuestas (>60%) y puede ser declarado sin sobresimplificación. Si no hay tal tema dominante, indica: "- Las respuestas ofrecen perspectivas diversas sin un único tema central dominante."
    - **Recomendación Clave para Avanzar:** Una única frase, **altamente accionable**, sugiriendo el paso inmediato más productivo para el investigador basado en el análisis completo (ej. "**El paso más útil ahora es investigar la discrepancia factual sobre [dato X específico] para clarificar su valor.**").

**## 2. Comparación Estructurada de Contribuciones de las IAs**

    **### 2.a. Afirmaciones Clave por IA:**
        - **`[AI_Modelo_X]` dice:**
            - Lista de 2 a 3 afirmaciones, argumentos, o puntos de datos concisos. Considera una afirmación como "importante" si es central al argumento de la IA para la `user_question`, y "distintiva" si ofrece una perspectiva única o datos no cubiertos ampliamente por otras. Prioriza datos verificables sobre opiniones generales.

    **### 2.b. Puntos de Consenso Directo (Acuerdo entre ≥2 IAs):**
        - Lista las afirmaciones o conclusiones clave donde dos o más IAs coinciden explícitamente o con muy alta similitud semántica.
        - Formato: `- [Afirmación de Consenso] (Apoyado por: [AI_Modelo_A], [AI_Modelo_C])`
        - Si no hay puntos de consenso directo fuerte, indica: "- **No se identificaron puntos de consenso directo fuerte entre las respuestas.**"

    **### 2.c. Contradicciones Factuales Evidentes:**
        - Lista cualquier contradicción directa en datos específicos verificables (ej. números, fechas, nombres, hechos objetivos).
        - Formato: `- [Hecho Disputado]: [AI_Modelo_A] afirma '[Valor A]', mientras que [AI_Modelo_B] afirma '[Valor B]'`
        - Si no hay contradicciones factuales evidentes, indica: "- **No se identificaron contradicciones factuales evidentes en los datos presentados.**"

    **### 2.d. Mapeo de Énfasis y Cobertura Temática Diferencial:**
        - Para cada `AI_Modelo_X`: Resume en 1-2 frases su enfoque principal, el ángulo que tomó, o el aspecto/sub-tema que más enfatizó al abordar la `user_question`.
        - **Omisiones Notables:** Lista 1-2 subtemas relevantes que fueron significativamente poco tratados o completamente omitidos por la mayoría de las IAs. Ejemplo: "- **El impacto económico a largo plazo fue un tema notablemente omitido por la mayoría de las respuestas.**"

**## 3. Puntos de Interés para Exploración (Accionables)**

    **### 3.a. Preguntas Sugeridas para Clarificación o Profundización:**
        - Formato: `- Pregunta Sugerida X: [Texto de la pregunta]`
        - Basado en contradicciones factuales, afirmaciones ambiguas/incompletas, o áreas que requieran mayor detalle, formula de 1 a 2 preguntas específicas y concisas. Estas deben fomentar el pensamiento crítico o la búsqueda de mayor profundidad por parte del usuario.
        - *Ejemplo:* "- Pregunta Sugerida 1: Dada la discrepancia en la tasa de crecimiento mencionada por [AI_Modelo_A] y [AI_Modelo_C], ¿cuáles son las metodologías o fuentes primarias que sustentan cada una de estas cifras divergentes?"

    **### 3.b. Áreas Potenciales para Mayor Investigación (Lagunas u Oportunidades de Extensión):**
        - Formato: `- Área de Exploración X: [Descripción del área y una potencial primera pregunta/acción para investigarla]`
        - Basado en omisiones temáticas o en la combinación de diferentes respuestas, señala 1-2 áreas no exploradas completamente pero que parecen relevantes o extensiones lógicas.
        - *Ejemplo:* "- Área de Exploración 1: Investigar las implicaciones éticas de [Aspecto Z], omitido por las IAs, comenzando por la pregunta: ¿Cómo [Aspecto Z] podría afectar a [Grupo Y]?"

    **### 3.c. Conexiones Implícitas Simples (Si existen con Alta Confianza y son Accionables):**
        - Formato: `- Posible Conexión a Explorar: El [Concepto P mencionado por AI_Modelo_A] y el [Concepto Q descrito por AI_Modelo_C] podrían estar interconectados debido a [explicación concisa de 1-2 frases]. Esto sugiere investigar si [pregunta/acción resultante].`
        - Solo destacar conexiones que sean muy directas, se puedan explicar muy concisamente, y ofrezcan una clara vía de exploración.

**## 4. Auto-Validación Interna de esta Síntesis (Checklist):**
    - `- Relevancia de Claims: ¿Cada 'Afirmación Clave por IA' (2.a) responde directamente a la user_question?`
    - `- Consenso Genuino: ¿Los 'Puntos de Consenso Directo' (2.b) reflejan un acuerdo real y no solo similitudes temáticas vagas?`
    - `- Contradicciones Claras: ¿Las 'Contradicciones Factuales Evidentes' (2.c) son inequívocamente sobre datos objetivos?`
    - `- Accionabilidad de Preguntas: ¿Las 'Preguntas Sugeridas' (3.a) son específicas y pueden guiar una acción o investigación?`
    - `- Síntesis General: ¿El 'Resumen Conciso General' (1) captura realmente un tema dominante si existe?`
    - `- Adherencia a Límites: ¿Se ha respetado el objetivo de longitud total del output?`
    - `- Claridad y Objetividad: ¿El tono general es neutral y la información fácil de entender?`

---

**INPUT DATA:**

**user_question:** [La pregunta del usuario se inferirá del contexto de las respuestas]

**external_ai_responses:**
{external_ai_responses}

Por favor, genera el meta-análisis siguiendo exactamente la estructura especificada arriba."""

        return prompt
    
    def get_synthesis_prompt(self, responses: List[StandardAIResponse]) -> str:
        """Método público para obtener el prompt de síntesis (para guardar en BD)"""
        return self._create_synthesis_prompt(responses)
    
    def _extract_synthesis_components(self, synthesis_text: str) -> Dict[str, Any]:
        """Extrae componentes estructurados de la síntesis v2.0 con meta-análisis profesional"""
        components = {
            "key_themes": [],
            "contradictions": [],
            "consensus_areas": [],
            "source_references": {},
            "recommendations": [],
            "suggested_questions": [],
            "research_areas": [],
            "connections": [],
            "meta_analysis_quality": "unknown"
        }
        
        try:
            # Buscar secciones específicas del nuevo formato v2.0
            sections = synthesis_text.split("##")
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                # 1. Resumen Conciso General y Recomendación Clave
                if "resumen conciso" in section.lower() or "recomendación clave" in section.lower():
                    lines = section.split("\n")[1:]
                    for line in lines:
                        line = line.strip()
                        if line and "recomendación clave" in line.lower():
                            # Extraer recomendación clave
                            rec = line.split(":")[-1].strip()
                            if rec:
                                components["recommendations"].append(rec)
                        elif line.startswith("- ") and "recomendación" not in line.lower():
                            # Extraer temas del resumen conciso
                            theme = line.lstrip("- ").strip()
                            if theme and len(theme) > 20:  # Solo temas sustanciales
                                components["key_themes"].append(theme)
                
                # 2.a. Afirmaciones Clave por IA
                elif "afirmaciones clave" in section.lower() and "por ia" in section.lower():
                    lines = section.split("\n")[1:]
                    current_ai = None
                    for line in lines:
                        line = line.strip()
                        if line.startswith("**[AI_Modelo_") and "] dice:**" in line:
                            # Extraer nombre de la IA
                            import re
                            ai_match = re.search(r'\*\*\[AI_Modelo_([^\]]+)\]', line)
                            if ai_match:
                                current_ai = ai_match.group(1)
                                if current_ai not in components["source_references"]:
                                    components["source_references"][current_ai] = []
                        elif line.startswith("- ") and current_ai:
                            # Extraer afirmación de la IA actual
                            claim = line.lstrip("- ").strip()
                            if claim:
                                components["source_references"][current_ai].append(claim)
                
                # 2.b. Puntos de Consenso Directo
                elif "puntos de consenso" in section.lower() or "consenso directo" in section.lower():
                    lines = section.split("\n")[1:]
                    for line in lines:
                        line = line.strip()
                        if line.startswith("- ") and "apoyado por:" in line.lower():
                            # Extraer punto de consenso
                            consensus_point = line.split("(Apoyado por:")[0].lstrip("- ").strip()
                            if consensus_point and "no se identificaron" not in consensus_point.lower():
                                components["consensus_areas"].append(consensus_point)
                
                # 2.c. Contradicciones Factuales Evidentes
                elif "contradicciones factuales" in section.lower() or "contradicciones evidentes" in section.lower():
                    lines = section.split("\n")[1:]
                    for line in lines:
                        line = line.strip()
                        if line.startswith("- ") and ("afirma" in line.lower() or "dice" in line.lower()):
                            # Extraer contradicción factual
                            contradiction = line.lstrip("- ").strip()
                            if contradiction and "no se identificaron" not in contradiction.lower():
                                components["contradictions"].append(contradiction)
                
                # 2.d. Mapeo de Énfasis y Cobertura Temática
                elif "mapeo de énfasis" in section.lower() or "cobertura temática" in section.lower():
                    lines = section.split("\n")[1:]
                    for line in lines:
                        line = line.strip()
                        if line.startswith("- ") and "omisiones notables" not in line.lower():
                            # Extraer énfasis temático como tema clave
                            theme = line.lstrip("- ").strip()
                            if theme:
                                components["key_themes"].append(theme)
                        elif line.startswith("**[AI_Modelo_") and "]:" in line:
                            # Extraer descripción del enfoque de cada IA como tema
                            ai_focus = line.split(":", 1)[-1].strip()
                            if ai_focus and len(ai_focus) > 10:
                                components["key_themes"].append(ai_focus)
                
                # 3.a. Preguntas Sugeridas
                elif "preguntas sugeridas" in section.lower():
                    lines = section.split("\n")[1:]
                    for line in lines:
                        line = line.strip()
                        if line.startswith("- Pregunta Sugerida"):
                            # Extraer pregunta sugerida
                            question = line.split(":", 1)[-1].strip()
                            if question:
                                components["suggested_questions"].append(question)
                
                # 3.b. Áreas Potenciales para Mayor Investigación
                elif "áreas potenciales" in section.lower() or "mayor investigación" in section.lower():
                    lines = section.split("\n")[1:]
                    for line in lines:
                        line = line.strip()
                        if line.startswith("- Área de Exploración"):
                            # Extraer área de investigación
                            area = line.split(":", 1)[-1].strip()
                            if area:
                                components["research_areas"].append(area)
                
                # 3.c. Conexiones Implícitas
                elif "conexiones implícitas" in section.lower():
                    lines = section.split("\n")[1:]
                    for line in lines:
                        line = line.strip()
                        if line.startswith("- Posible Conexión"):
                            # Extraer conexión implícita
                            connection = line.split(":", 1)[-1].strip()
                            if connection:
                                components["connections"].append(connection)
                
                # 4. Auto-Validación (para evaluar calidad del meta-análisis)
                elif "auto-validación" in section.lower() or "checklist" in section.lower():
                    # Contar elementos del checklist para evaluar completitud
                    checklist_items = len([line for line in section.split("\n") if line.strip().startswith("- ")])
                    if checklist_items >= 6:
                        components["meta_analysis_quality"] = "complete"
                    elif checklist_items >= 4:
                        components["meta_analysis_quality"] = "partial"
                    else:
                        components["meta_analysis_quality"] = "incomplete"
        
        except Exception as e:
            logger.warning(f"Error extrayendo componentes de síntesis v2.0: {e}")
            components["meta_analysis_quality"] = "error"
        
        return components
    
    def _validate_synthesis_quality(self, synthesis_text: str) -> tuple[bool, str]:
        """
        Validación específica para Tarea 3.3: Formato y Validación de la Respuesta Sintetizada
        
        Returns:
            tuple[bool, str]: (es_válida, razón_si_no_válida)
        """
        if not synthesis_text or not synthesis_text.strip():
            return False, "Síntesis vacía o solo espacios en blanco"
        
        cleaned_text = synthesis_text.strip()
        
        # 1. Validar longitud mínima razonable
        MIN_LENGTH = 80  # Reducido de 100 a 80 para ser más flexible
        if len(cleaned_text) < MIN_LENGTH:
            return False, f"Síntesis demasiado corta ({len(cleaned_text)} caracteres, mínimo {MIN_LENGTH})"
        
        # 2. Validar longitud máxima razonable (antes de otras validaciones complejas)
        MAX_LENGTH = 5000  # Aumentado para meta-análisis v2.0 extenso
        if len(cleaned_text) > MAX_LENGTH:
            return False, f"Síntesis demasiado larga ({len(cleaned_text)} caracteres, máximo {MAX_LENGTH})"
        
        # 3. Validar que no sea solo texto repetitivo
        words = cleaned_text.lower().split()
        unique_words = set(words)
        if len(words) > 8 and len(unique_words) / len(words) < 0.45:  # Menos del 45% de palabras únicas
            return False, "Síntesis demasiado repetitiva"
        
        # 4. Detectar si es solo un disclaimer del LLM
        disclaimer_phrases = [
            "no puedo", "no soy capaz", "no tengo la capacidad",
            "lo siento", "disculpa", "perdón",
            "no tengo acceso", "no puedo acceder",
            "como modelo de lenguaje", "como IA", "soy una IA",
            "no puedo proporcionar", "no puedo ofrecer",
            "disclaimer", "aviso", "descargo de responsabilidad",
            "consulta a un profesional", "busca asesoría profesional",
            "no soy un experto", "no soy profesional"
        ]
        
        disclaimer_count = sum(1 for phrase in disclaimer_phrases if phrase.lower() in cleaned_text.lower())
        total_words = len(cleaned_text.split())
        
        # Si más del 30% del contenido son disclaimers, es inválida
        if disclaimer_count > 3 or (disclaimer_count > 1 and total_words < 30):
            return False, f"Síntesis dominada por disclaimers ({disclaimer_count} frases de disclaimer detectadas)"
        
        # 5. Validar que tenga contenido sustancial
        # Debe tener al menos algunas oraciones completas
        sentences = [s.strip() for s in cleaned_text.split('.') if s.strip() and len(s.strip()) > 10]
        if len(sentences) < 2:  # Reducido de 3 a 2 para ser más flexible
            return False, f"Síntesis con muy pocas oraciones completas ({len(sentences)})"
        
        # 6. Validar que tenga estructura mínima (para síntesis estructuradas)
        has_structure = any(marker in cleaned_text for marker in ['##', '**', '- ', '1.', '2.', '•'])
        has_content_words = any(word in cleaned_text.lower() for word in [
            'según', 'menciona', 'indica', 'afirma', 'establece', 'tema', 'punto', 'aspecto', 'python'
        ])
        
        if not has_structure and not has_content_words and len(words) > 30:
            return False, "Síntesis carece de estructura o contenido analítico identificable"
        
        return True, "Síntesis válida"
    
    def _assess_synthesis_quality(self, synthesis_text: str, components: Dict[str, Any]) -> SynthesisQuality:
        """Evalúa la calidad de la síntesis v2.0 con meta-análisis profesional"""
        
        # Primero usar la validación formal de la Tarea 3.3
        is_valid, validation_reason = self._validate_synthesis_quality(synthesis_text)
        
        if not is_valid:
            logger.warning(f"Síntesis v2.0 no válida: {validation_reason}")
            return SynthesisQuality.FAILED
        
        # Si pasa la validación básica, evaluar calidad del meta-análisis v2.0
        if not synthesis_text or len(synthesis_text.strip()) < 200:  # Meta-análisis requiere más contenido
            return SynthesisQuality.FAILED
        
        # Contar disclaimers excesivos (criterio más estricto para meta-análisis)
        disclaimer_words = ["no puedo", "no sé", "disculpa", "lo siento", "disclaimer"]
        disclaimer_count = sum(1 for word in disclaimer_words if word in synthesis_text.lower())
        
        if disclaimer_count > 2:
            return SynthesisQuality.LOW
        
        # Verificar estructura y contenido del meta-análisis v2.0
        has_summary = "resumen conciso" in synthesis_text.lower() or "recomendación clave" in synthesis_text.lower()
        has_structured_analysis = "afirmaciones clave" in synthesis_text.lower() and "por ia" in synthesis_text.lower()
        has_consensus_analysis = "puntos de consenso" in synthesis_text.lower() or "consenso directo" in synthesis_text.lower()
        has_contradictions_analysis = "contradicciones factuales" in synthesis_text.lower() or "contradicciones evidentes" in synthesis_text.lower()
        has_exploration_points = "preguntas sugeridas" in synthesis_text.lower() or "áreas potenciales" in synthesis_text.lower()
        has_checklist = "auto-validación" in synthesis_text.lower() or "checklist" in synthesis_text.lower()
        
        # Verificar presencia de componentes extraídos
        has_recommendations = len(components.get("recommendations", [])) > 0
        has_questions = len(components.get("suggested_questions", [])) > 0
        has_research_areas = len(components.get("research_areas", [])) > 0
        has_ai_references = len(components.get("source_references", {})) > 0
        
        # Criterios para HIGH quality (meta-análisis completo)
        structure_score = sum([has_summary, has_structured_analysis, has_consensus_analysis, 
                              has_contradictions_analysis, has_exploration_points, has_checklist])
        content_score = sum([has_recommendations, has_questions, has_research_areas, has_ai_references])
        
        if structure_score >= 5 and content_score >= 3 and len(synthesis_text) > 800:
            return SynthesisQuality.HIGH
        # Criterios para MEDIUM quality (meta-análisis parcial pero útil)
        elif structure_score >= 3 and content_score >= 2 and len(synthesis_text) > 400:
            return SynthesisQuality.MEDIUM
        else:
            return SynthesisQuality.LOW
    
    def _select_best_fallback_response(self, responses: List[StandardAIResponse]) -> str:
        """Selecciona la mejor respuesta individual como fallback"""
        successful_responses = [
            r for r in responses 
            if r.status == AIResponseStatus.SUCCESS and r.response_text
        ]
        
        if not successful_responses:
            return "No se pudieron obtener respuestas útiles de los proveedores de IA."
        
        # Priorizar por longitud y proveedor
        def score_response(response):
            score = len(response.response_text or "")
            
            # Bonus por proveedor (preferir OpenAI > Anthropic para fallback)
            if response.ia_provider_name == AIProviderEnum.OPENAI:
                score += 100
            elif response.ia_provider_name == AIProviderEnum.ANTHROPIC:
                score += 50
            
            return score
        
        best_response = max(successful_responses, key=score_response)
        
        return f"""**Respuesta seleccionada de {best_response.ia_provider_name.value.upper()}:**

{best_response.response_text}

*Nota: Se muestra la mejor respuesta individual debido a que no se pudo generar una síntesis automática.*"""
    
    async def synthesize_responses(self, responses: List[StandardAIResponse]) -> ModeratorResponse:
        """
        Sintetiza múltiples respuestas de IA en una respuesta unificada.
        """
        start_time = datetime.utcnow()
        
        # Validar entrada
        if not responses:
            return ModeratorResponse(
                synthesis_text="No se recibieron respuestas para sintetizar.",
                quality=SynthesisQuality.FAILED,
                key_themes=[],
                contradictions=[],
                consensus_areas=[],
                source_references={},
                recommendations=[],
                suggested_questions=[],
                research_areas=[],
                connections=[],
                meta_analysis_quality="error",
                processing_time_ms=0,
                fallback_used=True,
                original_responses_count=0,
                successful_responses_count=0
            )
        
        successful_responses = [
            r for r in responses 
            if r.status == AIResponseStatus.SUCCESS and r.response_text
        ]
        
        # Caso: Sin respuestas útiles
        if not successful_responses:
            fallback_text = self._select_best_fallback_response(responses)
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return ModeratorResponse(
                synthesis_text=fallback_text,
                quality=SynthesisQuality.LOW,
                key_themes=[],
                contradictions=[],
                consensus_areas=[],
                source_references={},
                recommendations=[],
                suggested_questions=[],
                research_areas=[],
                connections=[],
                meta_analysis_quality="error",
                processing_time_ms=processing_time,
                fallback_used=True,
                original_responses_count=len(responses),
                successful_responses_count=0
            )
        
        # Caso: Solo una respuesta exitosa
        if len(successful_responses) == 1:
            response = successful_responses[0]
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return ModeratorResponse(
                synthesis_text=f"**Respuesta única de {response.ia_provider_name.value.upper()}:**\n\n{response.response_text}",
                quality=SynthesisQuality.MEDIUM,
                key_themes=["Respuesta única disponible"],
                contradictions=[],
                consensus_areas=[],
                source_references={response.ia_provider_name.value: ["Respuesta completa"]},
                recommendations=[],
                suggested_questions=[],
                research_areas=[],
                connections=[],
                meta_analysis_quality="unknown",
                processing_time_ms=processing_time,
                fallback_used=False,
                original_responses_count=len(responses),
                successful_responses_count=1
            )
        
        # Caso principal: Múltiples respuestas - Generar síntesis
        if not self.synthesis_adapter:
            # Fallback si no hay adaptador de síntesis
            fallback_text = self._select_best_fallback_response(responses)
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return ModeratorResponse(
                synthesis_text=fallback_text,
                quality=SynthesisQuality.LOW,
                key_themes=[],
                contradictions=[],
                consensus_areas=[],
                source_references={},
                recommendations=[],
                suggested_questions=[],
                research_areas=[],
                connections=[],
                meta_analysis_quality="error",
                processing_time_ms=processing_time,
                fallback_used=True,
                original_responses_count=len(responses),
                successful_responses_count=len(successful_responses)
            )
        
        try:
            # Crear prompt para síntesis
            synthesis_prompt = self._create_synthesis_prompt(responses)
            
            if not synthesis_prompt:
                raise ValueError("No se pudo crear prompt de síntesis")
            
            # Solicitar síntesis al LLM
            synthesis_request = AIRequest(
                prompt=synthesis_prompt,
                max_tokens=1200,  # Aumentado para meta-análisis v2.0 de 800-1000 tokens
                temperature=0.3,  # Baja temperatura para consistencia
                system_message="Eres un asistente de meta-análisis objetivo, analítico y altamente meticuloso. Genera reportes estructurados, claros y accionables siguiendo exactamente la estructura especificada."
            )
            
            synthesis_response = await self.synthesis_adapter.generate_response(synthesis_request)
            
            if synthesis_response.status != AIResponseStatus.SUCCESS or not synthesis_response.response_text:
                raise ValueError(f"Síntesis falló: {synthesis_response.error_message}")
            
            # Procesar la síntesis
            synthesis_text = synthesis_response.response_text.strip()
            components = self._extract_synthesis_components(synthesis_text)
            quality = self._assess_synthesis_quality(synthesis_text, components)
            
            # Si la calidad es muy baja, usar fallback
            if quality == SynthesisQuality.FAILED:
                raise ValueError("Calidad de síntesis insuficiente")
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return ModeratorResponse(
                synthesis_text=synthesis_text,
                quality=quality,
                key_themes=components["key_themes"],
                contradictions=components["contradictions"],
                consensus_areas=components["consensus_areas"],
                source_references=components["source_references"],
                recommendations=components["recommendations"],
                suggested_questions=components["suggested_questions"],
                research_areas=components["research_areas"],
                connections=components["connections"],
                meta_analysis_quality=components["meta_analysis_quality"],
                processing_time_ms=processing_time,
                fallback_used=False,
                original_responses_count=len(responses),
                successful_responses_count=len(successful_responses)
            )
        
        except Exception as e:
            logger.error(f"Error en síntesis automática: {e}")
            
            # Fallback a mejor respuesta individual
            fallback_text = self._select_best_fallback_response(responses)
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return ModeratorResponse(
                synthesis_text=fallback_text,
                quality=SynthesisQuality.LOW,
                key_themes=[],
                contradictions=[],
                consensus_areas=[],
                source_references={},
                recommendations=[],
                suggested_questions=[],
                research_areas=[],
                connections=[],
                meta_analysis_quality="error",
                processing_time_ms=processing_time,
                fallback_used=True,
                original_responses_count=len(responses),
                successful_responses_count=len(successful_responses)
            )
    
    async def close(self):
        """Cierra las conexiones del moderador"""
        if self.synthesis_adapter and hasattr(self.synthesis_adapter, 'close'):
            await self.synthesis_adapter.close() 