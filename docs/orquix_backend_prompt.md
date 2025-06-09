# Prompt para Cursor — Backend Orquix MVP (Contexto y Funcionamiento)

## CONTEXTO DEL PROYECTO
Estoy desarrollando el backend de Orquix v0.1 (MVP). Es una plataforma de investigación inteligente que permite a un usuario hacer preguntas dentro de un proyecto y recibir respuestas unificadas por una IA Moderadora, que sintetiza las respuestas generadas por múltiples IAs comerciales.

Stack tecnológico:
- Python 3.12, FastAPI, SQLModel, PostgreSQL 15 con pgvector
- Gestión de dependencias con poetry, migraciones con Alembic
- Llamadas a IAs externas con httpx (async)
- Embeddings locales con sentence-transformers o remotos vía OpenAI
- API documentada con FastAPI + Pydantic

---

## FUNCIONAMIENTO DEL SISTEMA (FLUJO MVP)
Cuando el usuario envía una nueva pregunta (`user_prompt_text`), el sistema sigue este flujo:

1. **Búsqueda de contexto relevante**:
   - El texto del prompt se convierte en un embedding vectorial.
   - Se realiza una búsqueda de similitud en la tabla `context_chunks` (filtrando por `project_id`).
   - Se recuperan los K chunks más relevantes.

2. **Construcción de bloque de contexto**:
   - Se concatena el contenido de los chunks en un solo string (máx. 3000 tokens).
   - Se añade también el historial reciente (últimos N prompts y respuestas del proyecto) como memoria conversacional.
   - Esto da como resultado un prompt enriquecido.

3. **Consulta a múltiples IAs (orquestador)**:
   - El prompt enriquecido se envía simultáneamente a dos IAs comerciales: GPT-4o-mini (OpenAI) y Claude 3 Haiku (Anthropic).
   - Cada IA tiene su propio adaptador (payload, formato, headers, etc.).
   - Las llamadas son asíncronas y con timeout.

4. **Moderación IA (síntesis)**:
   - Las respuestas crudas de cada IA se procesan por el Moderador IA.
   - El moderador usa un LLM económico (como GPT-3.5-Turbo) para generar una síntesis extractiva:
     - Resalta los 2-3 puntos principales
     - Detecta contradicciones obvias
     - Produce una respuesta final clara y útil

5. **Persistencia y retorno**:
   - Todo se guarda en la base de datos:
     - `InteractionEvent` con la pregunta, contexto usado y referencia a la síntesis
     - `IAResponse` para cada IA
     - `ModeratedSynthesis` con el texto final
     - Nuevos `ContextChunk` si aplica
   - Se devuelve al frontend la síntesis final y, opcionalmente, las respuestas IA individuales.

---

## MODELOS CENTRALES (RESUMEN)
- `User`, `Project`
- `InteractionEvent`: cada consulta individual
- `IAResponse`: una respuesta de una IA
- `ModeratedSynthesis`: resultado del moderador
- `ContextChunk`: cualquier texto convertido a vector para búsqueda

---

## INPUT Y OUTPUT CLAVE PARA EL ENDPOINT `/api/projects/{project_id}/query`

### Entrada:
```json
{
  "user_prompt_text": "Dame los últimos 4 días del itinerario",
  "project_id": "uuid-del-proyecto"
}
```

### Salida:
```json
{
  "moderated_synthesis": "Aquí tienes un resumen de los últimos 4 días...",
  "ia_responses": [
    {
      "ia_provider_name": "OpenAI_GPT-4o-mini",
      "response_text": "...",
      "latency_ms": 1432
    },
    {
      "ia_provider_name": "Anthropic_Claude-3-Haiku",
      "response_text": "...",
      "latency_ms": 1256
    }
  ]
}
```

---

## CONSIDERACIONES GENERALES
- Cada componente debe estar desacoplado: `ContextManager`, `AIOrchestrator`, `Moderator`
- Se usarán servicios internos (`app/services/`) para la lógica, no en los routers directamente
- La BD se consulta de forma asíncrona (asyncpg + SQLModel)
- Todos los tokens/jwt vendrán de NextAuth.js; el user_id debe extraerse desde allí
- Queremos tests con `pytest-asyncio` y `httpx.AsyncClient`

---

## INSTRUCCIONES PARA CURSOR
1. Entiende esta arquitectura antes de escribir código.
2. Cuando escribas lógica de orquestación o endpoints, sigue este flujo completo.
3. Si vas a trabajar sobre un módulo, dime cuál (ContextManager, Orchestrator, Moderator, API Gateway).
