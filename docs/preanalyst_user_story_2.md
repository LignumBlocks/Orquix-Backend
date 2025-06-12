# Historia de Usuario: Interpretación previa de la pregunta (PreAnalystService)

## Contexto
En Orquix, queremos que antes de mandar una pregunta del usuario a las IAs externas, el sistema (el “bicho”) primero analice e interprete la intención del usuario. Esto es especialmente útil en la primera pregunta de una sesión, donde el usuario puede ser ambigua, incompleta o no técnica.

## Objetivo
Crear un servicio `PreAnalystService` que tome el `user_prompt_text` como entrada y devuelva:

1. Una paráfrasis de lo que entiende el sistema.
2. Una lista de dudas o puntos que podría necesitar aclarar con el usuario.
3. Una versión “pregunta refinada” que representa lo que realmente se va a mandar a las IAs (solo si ya está claro).

Este servicio NO hace llamadas a otras IAs internas, pero sí puede usar un modelo económico de OpenAI como GPT-3.5-Turbo-1106.

---

## Input esperado
```json
{
  "user_prompt_text": "necesito ayuda con el presupuesto de mi viaje"
}
```

---

## Output esperado (ejemplo)
```json
{
  "interpreted_intent": "El usuario quiere asistencia para planificar el presupuesto de un viaje.",
  "clarification_questions": [
    "¿Cuál es el destino del viaje?",
    "¿Cuántos días planea viajar?",
    "¿Cuál es el presupuesto aproximado disponible?"
  ],
  "refined_prompt_candidate": null
}
```

(Si el usuario ya respondió todo eso, `clarification_questions = []` y sí se devuelve un `refined_prompt_candidate`)

---

## Detalles técnicos

- El servicio vivirá en `app/services/pre_analyst.py`
- Usará `openai.ChatCompletion.create()` con el modelo `gpt-3.5-turbo-1106`
- El sistema prompt será:

```python
SYSTEM_PROMPT = """Eres un asistente experto que ayuda a interpretar preguntas de usuarios sobre investigación, ideas o planificación. Tu tarea es:

1. Analizar la intención principal del usuario.
2. Identificar si hay datos faltantes o ambigüedades en la pregunta.
3. Proponer una pregunta mejorada solo si la información es suficiente.

Responde siempre en JSON válido con los siguientes campos:
- interpreted_intent: string (explica brevemente lo que el usuario quiere)
- clarification_questions: lista de strings (preguntas que ayudarían a mejorar la comprensión)
- refined_prompt_candidate: string o null (versión mejorada de la pregunta si está todo claro)
"""
```

- Ejemplo de llamada:

```python
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo-1106",
    temperature=0.3,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
)
```

---

## Consideraciones

- Esta funcionalidad es previa a `/api/projects/{project_id}/query`
- Si el usuario confirma la interpretación o responde las aclaraciones, entonces se inicia el flujo habitual (`ContextManager`, `Orchestrator`, etc.)
- Esto habilita referencias implícitas más adelante como “los últimos 4”

---

## Entregable esperado

- Archivo `pre_analyst.py` con una función pública:
```python
async def analyze_prompt(user_prompt_text: str) -> PreAnalysisResult
```

- Clase `PreAnalysisResult` con campos:
```python
class PreAnalysisResult(BaseModel):
    interpreted_intent: str
    clarification_questions: List[str]
    refined_prompt_candidate: Optional[str]
```

- El sistema debe ser fácilmente invocable desde una ruta `/analyze-prompt` en el futuro.
