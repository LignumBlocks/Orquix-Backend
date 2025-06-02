from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

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

class ModeratorRequest(BaseModel):
    """Solicitud al moderador para síntesis"""
    query: str
    responses_to_synthesize: List[Dict[str, Any]]  # Lista de respuestas normalizadas
    synthesis_strategy: str = "extractive_enhanced"  # Estrategia de síntesis
    max_synthesis_length: int = 250  # Máximo de palabras en la síntesis
    include_contradictions: bool = True
    include_source_references: bool = True 