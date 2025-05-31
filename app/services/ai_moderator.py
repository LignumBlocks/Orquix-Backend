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
    """Respuesta del moderador con síntesis y metadatos"""
    synthesis_text: str
    quality: SynthesisQuality
    key_themes: List[str]
    contradictions: List[str]
    consensus_areas: List[str]
    source_references: Dict[str, List[str]]  # provider -> list of points
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
        """Crea el prompt optimizado para síntesis extractiva"""
        
        # Filtrar solo respuestas exitosas
        successful_responses = [
            r for r in responses 
            if r.status == AIResponseStatus.SUCCESS and r.response_text
        ]
        
        if not successful_responses:
            return ""
        
        # Construir el prompt con las respuestas
        responses_text = ""
        for i, response in enumerate(successful_responses, 1):
            provider_name = response.ia_provider_name.value.upper()
            responses_text += f"\n--- RESPUESTA IA{i} ({provider_name}) ---\n"
            responses_text += response.response_text.strip()
            responses_text += "\n"
        
        prompt = f"""Eres un experto analista que debe sintetizar múltiples respuestas de IA en una síntesis coherente y útil.

RESPUESTAS A SINTETIZAR:{responses_text}

INSTRUCCIONES ESPECÍFICAS:
1. Identifica los 2-3 temas o puntos clave principales cubiertos por el conjunto de respuestas
2. Para cada tema/punto clave, resume brevemente la postura o aporte de cada IA que lo haya mencionado
3. Señala contradicciones factuales directas y obvias entre las respuestas
4. Formula una breve conclusión general si hay consenso claro, o nota sobre la divergencia principal
5. Intenta referenciar de qué IA proviene cada punto específico (ej. "según IA1...")

FORMATO DE RESPUESTA:
## Temas Clave Identificados
[Lista los 2-3 temas principales]

## Análisis por Tema
[Para cada tema, resume las posturas de cada IA]

## Contradicciones Detectadas
[Lista contradicciones factuales directas, o "Ninguna contradicción significativa detectada"]

## Síntesis Final
[Conclusión general de máximo 100 palabras]

RESTRICCIONES:
- Máximo 250 palabras en total
- Sé conciso pero preciso
- Evita disclaimers innecesarios
- Enfócate en el contenido factual
- Mantén un tono neutral y analítico"""

        return prompt
    
    def _extract_synthesis_components(self, synthesis_text: str) -> Dict[str, Any]:
        """Extrae componentes estructurados de la síntesis"""
        components = {
            "key_themes": [],
            "contradictions": [],
            "consensus_areas": [],
            "source_references": {}
        }
        
        try:
            # Buscar secciones específicas
            sections = synthesis_text.split("##")
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                if "temas clave" in section.lower():
                    # Extraer temas clave
                    lines = section.split("\n")[1:]  # Saltar el título
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Limpiar bullets y numeración
                            theme = line.lstrip("- *1234567890. ").strip()
                            if theme:
                                components["key_themes"].append(theme)
                
                elif "contradicciones" in section.lower():
                    # Extraer contradicciones
                    lines = section.split("\n")[1:]
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith("#") and "ninguna" not in line.lower():
                            contradiction = line.lstrip("- *1234567890. ").strip()
                            if contradiction:
                                components["contradictions"].append(contradiction)
                
                elif "síntesis final" in section.lower() or "conclusión" in section.lower():
                    # Extraer áreas de consenso del texto final
                    lines = section.split("\n")[1:]
                    consensus_text = " ".join(lines).strip()
                    if "consenso" in consensus_text.lower() or "acuerdo" in consensus_text.lower():
                        components["consensus_areas"].append(consensus_text)
            
            # Extraer referencias a IAs (IA1, IA2, etc.)
            import re
            ia_references = re.findall(r'IA\d+|según IA\d+', synthesis_text, re.IGNORECASE)
            for ref in ia_references:
                ia_num = re.search(r'\d+', ref).group()
                if f"IA{ia_num}" not in components["source_references"]:
                    components["source_references"][f"IA{ia_num}"] = []
        
        except Exception as e:
            logger.warning(f"Error extrayendo componentes de síntesis: {e}")
        
        return components
    
    def _assess_synthesis_quality(self, synthesis_text: str, components: Dict[str, Any]) -> SynthesisQuality:
        """Evalúa la calidad de la síntesis generada"""
        if not synthesis_text or len(synthesis_text.strip()) < 50:
            return SynthesisQuality.FAILED
        
        # Contar disclaimers excesivos
        disclaimer_words = ["no puedo", "no sé", "disculpa", "lo siento", "disclaimer"]
        disclaimer_count = sum(1 for word in disclaimer_words if word in synthesis_text.lower())
        
        if disclaimer_count > 2:
            return SynthesisQuality.LOW
        
        # Verificar estructura
        has_themes = len(components["key_themes"]) > 0
        has_structure = "##" in synthesis_text or len(synthesis_text.split("\n")) > 3
        
        if has_themes and has_structure and len(synthesis_text) > 100:
            return SynthesisQuality.HIGH
        elif has_structure or has_themes:
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
                max_tokens=400,  # Suficiente para 250 palabras + estructura
                temperature=0.3,  # Baja temperatura para consistencia
                system_message="Eres un analista experto en síntesis de información. Sé conciso, preciso y estructurado."
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
                processing_time_ms=processing_time,
                fallback_used=True,
                original_responses_count=len(responses),
                successful_responses_count=len(successful_responses)
            )
    
    async def close(self):
        """Cierra las conexiones del moderador"""
        if self.synthesis_adapter and hasattr(self.synthesis_adapter, 'close'):
            await self.synthesis_adapter.close() 