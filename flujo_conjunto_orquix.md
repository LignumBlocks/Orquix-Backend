# Flujo Conjunto: Context Builder + AI Orchestrator + AI Moderator

## Descripción General del Flujo

Orquix funciona en **2 fases principales**:
1. **Fase de Construcción de Contexto** (Context Builder)
2. **Fase de Consulta Principal** (AI Orchestrator + AI Moderator)

## Fase 1: Construcción de Contexto (Context Builder)

### Propósito
El usuario construye contexto conversacionalmente antes de hacer su consulta principal.

### Flujo Detallado
```
Usuario: "Tengo una startup de software dental"
Context Builder: 
  ├── Clasifica: INFORMATION
  ├── Extrae: "startup, software, gestión, clínicas dentales"
  ├── Actualiza contexto acumulado
  └── Sugiere: "¿En qué fase está tu startup?"

Usuario: "Estamos en fase beta con 5 clientes"
Context Builder:
  ├── Clasifica: INFORMATION  
  ├── Extrae: "fase beta, 5 clientes piloto"
  ├── Actualiza contexto: "Startup de software de gestión para clínicas dentales. En fase beta con 5 clientes piloto."
  └── Sugiere: "¿Cuál es tu principal desafío actual?"

Usuario: "¿Qué estrategias de marketing me recomiendas?"
Context Builder:
  ├── Clasifica: QUESTION
  └── Responde: "Basado en tu contexto, podrías considerar..."
```

### Comandos Especiales
```
Usuario: "resume lo que hemos hablado"
Context Builder: Ejecuta función summary() → "Startup de software dental en fase beta con 5 clientes"

Usuario: "muestra todo el contexto"
Context Builder: Ejecuta función show_context() → Contexto completo con estadísticas

Usuario: "borra el contexto"
Context Builder: Ejecuta función clear_context() → Contexto limpio
```

### Estado Final de Fase 1
```
Contexto Acumulado: "Startup de software de gestión para clínicas dentales. En fase beta con 5 clientes piloto. Principal desafío: adquisición de nuevos clientes."
```

## Transición: De Contexto a Consulta Principal

### Trigger de Transición
Cuando el usuario hace una **pregunta compleja** o **finaliza explícitamente** la construcción de contexto:

```
Usuario: "Ahora quiero que analices mi estrategia de marketing completa"
Sistema: Detecta → Consulta Principal → Activa Fase 2
```

## Fase 2: Consulta Principal (Orchestrator + Moderator)

### Entrada a Fase 2
```
Input:
├── user_prompt: "Analiza mi estrategia de marketing completa"
├── context_text: "Startup de software dental en fase beta con 5 clientes..."
└── project_id: UUID del proyecto
```

### Paso 1: AI Orchestrator - Orquestación Múltiple

#### Preparación del AIRequest
```python
ai_request = AIRequest(
    user_question="Analiza mi estrategia de marketing completa",
    context="Startup de software dental en fase beta con 5 clientes...",
    temperature=0.7,
    max_tokens=1000,
    system_prompt="Eres un consultor de marketing especializado..."
)
```

#### Ejecución Paralela (Estrategia FALLBACK por defecto)
```
AI Orchestrator:
├── Intenta OpenAI GPT-4o-mini
│   ├── Request: AIRequest + context
│   ├── Response: "Para tu startup dental, recomiendo..."
│   └── Status: SUCCESS ✅
│
├── Intenta Anthropic Claude 3 Haiku  
│   ├── Request: AIRequest + context
│   ├── Response: "Considerando tu fase beta, sugiero..."
│   └── Status: SUCCESS ✅
│
└── Resultado: 2 respuestas exitosas para síntesis
```

### Paso 2: AI Moderator - Síntesis Inteligente

#### Entrada al Moderator
```python
responses = [
    StandardAIResponse(
        ia_provider_name="OPENAI",
        response_text="Para tu startup dental, recomiendo: 1) Marketing de contenido educativo...",
        status=SUCCESS
    ),
    StandardAIResponse(
        ia_provider_name="ANTHROPIC", 
        response_text="Considerando tu fase beta, sugiero: 1) Testimonios de clientes actuales...",
        status=SUCCESS
    )
]
```

#### Generación de Meta-Análisis v2.0
```
AI Moderator:
├── Crea prompt de síntesis profesional
├── Solicita análisis a Claude 3 Haiku
├── Recibe reporte estructurado:
│   ├── ## 1. Resumen y Recomendación Clave
│   ├── ## 2. Comparación de Contribuciones
│   │   ├── 2.a. Afirmaciones por IA
│   │   ├── 2.b. Puntos de Consenso
│   │   ├── 2.c. Contradicciones
│   │   └── 2.d. Énfasis Diferencial
│   ├── ## 3. Puntos de Exploración
│   │   ├── 3.a. Preguntas Sugeridas
│   │   ├── 3.b. Áreas de Investigación
│   │   └── 3.c. Conexiones Implícitas
│   └── ## 4. Auto-Validación
├── Extrae componentes estructurados
├── Evalúa calidad: HIGH
└── Genera ModeratorResponse final
```

#### Síntesis Final Ejemplo
```markdown
## 1. Resumen Conciso General y Recomendación Clave
Las dos IAs coinciden en priorizar la credibilidad y educación para tu startup dental en fase beta.
**Recomendación Clave:** Implementar programa de testimonios de clientes actuales como primera prioridad.

## 2. Comparación Estructurada de Contribuciones

### 2.a. Afirmaciones Clave por IA:
**[AI_Modelo_OPENAI] dice:**
- Marketing de contenido educativo sobre gestión dental
- SEO local para clínicas dentales
- Webinars para demostrar el software

**[AI_Modelo_ANTHROPIC] dice:**
- Testimonios y casos de éxito de los 5 clientes beta
- Marketing directo a asociaciones dentales
- Freemium trial extendido

### 2.b. Puntos de Consenso Directo:
- Aprovechar los 5 clientes actuales como embajadores (Apoyado por: OPENAI, ANTHROPIC)
- Enfoque en credibilidad y confianza del sector dental (Apoyado por: OPENAI, ANTHROPIC)

### 2.c. Contradicciones Factuales Evidentes:
- **No se identificaron contradicciones factuales evidentes en los datos presentados.**

## 3. Puntos de Interés para Exploración

### 3.a. Preguntas Sugeridas:
- Pregunta Sugerida 1: ¿Cuál es el ROI actual de tus 5 clientes beta y cómo lo puedes cuantificar?
- Pregunta Sugerida 2: ¿Qué asociaciones dentales regionales podrían ser partners estratégicos?

### 3.b. Áreas Potenciales para Mayor Investigación:
- Área de Exploración 1: Investigar competencia directa en software dental, comenzando por análisis de pricing y features

## 4. Auto-Validación Interna de esta Síntesis:
- ✅ Relevancia de Claims: Cada afirmación responde directamente a estrategia de marketing
- ✅ Consenso Genuino: Los puntos de consenso reflejan acuerdo real sobre credibilidad
- ✅ Accionabilidad de Preguntas: Las preguntas sugeridas son específicas y ejecutables
```

## Resultado Final al Usuario

### Respuesta Completa
```json
{
  "synthesis_text": "## 1. Resumen Conciso General...",
  "quality": "HIGH",
  "key_themes": [
    "Marketing de contenido educativo",
    "Testimonios de clientes beta", 
    "Credibilidad en sector dental"
  ],
  "recommendations": [
    "Implementar programa de testimonios de clientes actuales"
  ],
  "suggested_questions": [
    "¿Cuál es el ROI actual de tus 5 clientes beta?",
    "¿Qué asociaciones dentales podrían ser partners?"
  ],
  "consensus_areas": [
    "Aprovechar los 5 clientes actuales como embajadores",
    "Enfoque en credibilidad del sector dental"
  ],
  "source_references": {
    "OPENAI": ["Marketing de contenido educativo", "SEO local", "Webinars"],
    "ANTHROPIC": ["Testimonios y casos de éxito", "Marketing a asociaciones", "Freemium trial"]
  },
  "processing_time_ms": 2847,
  "meta_analysis_quality": "complete"
}
```

## Ventajas del Flujo Conjunto

### 1. **Contexto Rico y Relevante**
- Context Builder acumula información específica del usuario
- AI Orchestrator usa este contexto para consultas más precisas
- AI Moderator sintetiza considerando el contexto completo

### 2. **Múltiples Perspectivas Sintetizadas**
- Orchestrator obtiene respuestas de OpenAI + Anthropic
- Moderator identifica consensos y contradicciones
- Usuario recibe análisis comparativo profesional

### 3. **Escalabilidad y Robustez**
- Context Builder: Function calling nativo (menos errores)
- Orchestrator: Estrategia FALLBACK (alta disponibilidad)
- Moderator: Validación de calidad (respuestas confiables)

### 4. **Experiencia de Usuario Fluida**
```
Fase 1: Conversación natural → Contexto acumulado
Transición: Pregunta compleja detectada
Fase 2: Análisis profesional → Síntesis estructurada
```

## Métricas del Flujo Completo

### Tiempos Típicos
- **Fase 1 (Context Builder)**: 500-800ms por intercambio
- **Fase 2 (Orchestrator)**: 1000-1500ms para múltiples IAs
- **Fase 2 (Moderator)**: 1500-3000ms para síntesis
- **Total Fase 2**: ~3-5 segundos para respuesta completa

### Calidad y Confiabilidad
- **Context Builder**: >95% precisión en clasificación
- **AI Orchestrator**: >95% disponibilidad con fallback
- **AI Moderator**: >85% síntesis de calidad HIGH/MEDIUM

## Estado Actual

✅ **Context Builder**: Refactorizado con function calling
✅ **AI Orchestrator**: 4 estrategias implementadas  
✅ **AI Moderator**: Meta-análisis v2.0 completo
✅ **Integración**: Flujo completo funcional
⚠️ **Configuración**: Pendiente revisión para deployment
