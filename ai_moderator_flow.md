# AI Moderator - Flujo Detallado

## Descripción General

El `AIModerator` es el componente que sintetiza respuestas de múltiples proveedores de IA usando **meta-análisis profesional v2.0**. Genera reportes estructurados de 800-1000 tokens con análisis comparativo, consensos, contradicciones y recomendaciones accionables.

## Arquitectura y Configuración

### Inicialización
```python
def __init__(self):
    self.synthesis_adapter = None
    self._initialize_synthesis_adapter()
```

### Adaptador de Síntesis (LLM Económico)
**Prioridad 1: Claude 3 Haiku** (más económico)
```python
if settings.ANTHROPIC_API_KEY:
    self.synthesis_adapter = AnthropicAdapter(
        api_key=settings.ANTHROPIC_API_KEY,
        model="claude-3-haiku-20240307"
    )
```

**Fallback: GPT-3.5-Turbo**
```python
if settings.OPENAI_API_KEY:
    self.synthesis_adapter = OpenAIAdapter(
        api_key=settings.OPENAI_API_KEY,
        model="gpt-3.5-turbo"
    )
```

## Modelo de Respuesta v2.0

### ModeratorResponse
```python
class ModeratorResponse(BaseModel):
    # Síntesis principal
    synthesis_text: str
    quality: SynthesisQuality  # HIGH | MEDIUM | LOW | FAILED
    
    # Componentes extraídos
    key_themes: List[str]
    contradictions: List[str]
    consensus_areas: List[str]
    source_references: Dict[str, List[str]]  # provider -> claims
    
    # Nuevos campos v2.0
    recommendations: List[str]
    suggested_questions: List[str]
    research_areas: List[str]
    connections: List[str]
    meta_analysis_quality: str  # complete | partial | incomplete | error
    
    # Metadatos
    processing_time_ms: int
    fallback_used: bool
    original_responses_count: int
    successful_responses_count: int
```

## Flujo Principal: synthesize_responses()

### Entrada
- `responses: List[StandardAIResponse]` - Respuestas de múltiples IAs

### Casos de Manejo

#### 1. Sin Respuestas
```python
if not responses:
    return ModeratorResponse(
        synthesis_text="No se recibieron respuestas para sintetizar.",
        quality=SynthesisQuality.FAILED,
        # ... campos vacíos
    )
```

#### 2. Sin Respuestas Exitosas
```python
if not successful_responses:
    fallback_text = self._select_best_fallback_response(responses)
    return ModeratorResponse(
        synthesis_text=fallback_text,
        quality=SynthesisQuality.LOW,
        fallback_used=True
    )
```

#### 3. Una Sola Respuesta
```python
if len(successful_responses) == 1:
    return ModeratorResponse(
        synthesis_text=f"**Respuesta única de {provider}:**\n\n{text}",
        quality=SynthesisQuality.MEDIUM,
        key_themes=["Respuesta única disponible"]
    )
```

#### 4. Múltiples Respuestas (Caso Principal)
1. Crear prompt de meta-análisis v2.0
2. Solicitar síntesis al LLM
3. Extraer componentes estructurados
4. Evaluar calidad
5. Retornar respuesta completa

## Prompt de Meta-Análisis v2.0

### Estructura del Prompt
El prompt genera un reporte de ~800-1000 tokens con estas secciones:

#### 0. Evaluación Inicial de Relevancia
- Identifica respuestas fuera de tema o irrelevantes

#### 1. Resumen Conciso General y Recomendación Clave
- Párrafo de 2-3 frases (máximo 50 palabras)
- **Recomendación Clave**: Paso inmediato más productivo

#### 2. Comparación Estructurada
- **2.a. Afirmaciones Clave por IA**: 2-3 puntos centrales por proveedor
- **2.b. Puntos de Consenso Directo**: Acuerdos entre ≥2 IAs
- **2.c. Contradicciones Factuales Evidentes**: Datos objetivos en conflicto
- **2.d. Mapeo de Énfasis y Cobertura**: Enfoques y omisiones notables

#### 3. Puntos de Interés para Exploración
- **3.a. Preguntas Sugeridas**: Para clarificación/profundización
- **3.b. Áreas de Investigación**: Lagunas y oportunidades
- **3.c. Conexiones Implícitas**: Interrelaciones entre conceptos

#### 4. Auto-Validación Interna
- Checklist de calidad del meta-análisis

## Extracción de Componentes

### _extract_synthesis_components()
Parsea la síntesis estructurada y extrae:

```python
components = {
    "key_themes": [],           # Temas principales
    "contradictions": [],       # Contradicciones factuales
    "consensus_areas": [],      # Puntos de acuerdo
    "source_references": {},    # provider -> claims
    "recommendations": [],      # Recomendaciones clave
    "suggested_questions": [], # Preguntas sugeridas
    "research_areas": [],      # Áreas de investigación
    "connections": [],         # Conexiones implícitas
    "meta_analysis_quality": "unknown"
}
```

## Validación de Calidad

### _validate_synthesis_quality()
**Criterios de validación:**
- Longitud mínima: 80 caracteres
- Longitud máxima: 5000 caracteres
- Diversidad de palabras: >45% únicas
- Detección de disclaimers excesivos
- Mínimo 2 oraciones completas
- Estructura o contenido analítico identificable

### _assess_synthesis_quality()
**Niveles de calidad:**

#### HIGH Quality
- 5+ secciones estructurales presentes
- 3+ tipos de contenido extraído
- >800 caracteres de síntesis
- Meta-análisis completo

#### MEDIUM Quality  
- 3+ secciones estructurales
- 2+ tipos de contenido
- >400 caracteres
- Meta-análisis parcial pero útil

#### LOW Quality
- Estructura mínima
- Contenido básico
- Síntesis simple

#### FAILED Quality
- No pasa validación básica
- Demasiados disclaimers
- Contenido insuficiente

## Configuración de Síntesis

### Parámetros del AIRequest
```python
synthesis_request = AIRequest(
    prompt=synthesis_prompt,
    max_tokens=1200,  # Aumentado para meta-análisis v2.0
    temperature=0.3,  # Baja temperatura para consistencia
    system_message="Eres un asistente de meta-análisis objetivo..."
)
```

## Integración con el Sistema

### Uso desde Projects Endpoint
```python
# En projects.py - Paso 3: Síntesis
with time_step(interaction_id, "synthesis") as timer:
    synthesis_result = await synthesize_responses(
        moderator=moderator,
        ai_responses=orchestration_result.ai_responses,
        project_id=project_id,
        interaction_id=interaction_id
    )
```

## Fallback Strategy

### _select_best_fallback_response()
Cuando la síntesis falla:
1. Filtra respuestas exitosas
2. Puntúa por longitud y proveedor
3. Prioriza OpenAI > Anthropic
4. Retorna mejor respuesta individual con nota explicativa

## Métricas y Monitoreo

### Métricas Capturadas
- **Tiempo de procesamiento**: processing_time_ms
- **Tasa de éxito**: successful vs failed synthesis
- **Calidad de síntesis**: HIGH/MEDIUM/LOW/FAILED distribution
- **Uso de fallback**: fallback_used frequency
- **Completitud del meta-análisis**: meta_analysis_quality

### Logging
```python
logger.info("Moderador inicializado con Claude 3 Haiku")
logger.warning(f"Error en síntesis automática: {e}")
logger.error(f"Síntesis v2.0 no válida: {validation_reason}")
```

## Estado Actual y Rendimiento

### Estadísticas Típicas
- **Tiempo de síntesis**: 1500-3000ms
- **Tasa de éxito**: >85% con fallback
- **Calidad promedio**: MEDIUM-HIGH
- **Costo por síntesis**: ~$0.002-0.005 (Claude Haiku)

### Próximas Mejoras
- [ ] Caching de síntesis similares
- [ ] Templates de síntesis por dominio
- [ ] Métricas de satisfacción de usuario
- [ ] Optimización de prompts por tipo de consulta
