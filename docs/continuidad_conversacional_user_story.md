# Historia de Usuario: Continuidad Conversacional Posterior a la Síntesis (PostQuery Follow-up)

## Contexto
Orquix no debe comportarse como un sistema de “pregunta-respuesta única”. Según lo planteado por Nelson, debe ser un asistente inteligente que acompaña al usuario durante una investigación. Esto implica que, luego de entregar una respuesta sintetizada basada en múltiples IAs, Orquix debe mantener el hilo conversacional y estar preparado para continuar el análisis.

## Objetivo
Permitir que Orquix:
1. Entienda que la respuesta sintetizada es el inicio de una conversación, no el final.
2. Pueda recibir nuevas consultas relacionadas con la anterior.
3. Use lo que se generó en la interacción previa como base semántica (memoria activa).
4. Adapte automáticamente el contexto sin forzar al usuario a repetir o reexplicar lo que ya se resolvió.

---

## Escenario

**Consulta inicial del usuario:**
> “Necesito ayuda para planear un viaje de 5 días a Cuba con mi esposa”

**Proceso:**
- Orquix interpreta, aclara y refina la pregunta
- Consulta a las IAs
- El moderador genera una síntesis

**Respuesta:**
> “Aquí están las mejores opciones para un viaje de 5 días en Cuba con tu esposa…”

**Consulta siguiente del usuario:**
> “¿Y si fuéramos con niños?”

---

## Comportamiento esperado del sistema

- El sistema debe interpretar que la nueva pregunta **se refiere a lo ya dicho anteriormente**
- Debe recuperar:
  - La pregunta refinada anterior
  - La respuesta del moderador
  - Los aportes individuales de las IAs (si es útil)
- Generar un nuevo prompt enriquecido que considere:
  - “Viaje a Cuba por 5 días con niños”
  - Lo que ya se dijo (para evitar repetir)
- Repetir el ciclo: enviar a IAs → sintetizar → responder

---

## Consideraciones técnicas

- Se requiere una forma de identificar la última interacción significativa (última `interaction_event`)
- Se puede usar:
  - `project_id` y `user_id` para filtrar eventos recientes
  - `created_at` para priorizar
- Idealmente se puede incluir la última `moderated_synthesis` como parte del nuevo contexto

---

## Entregable esperado

- Funcionalidad que permita a `/query` (o un endpoint equivalente) considerar automáticamente el historial inmediato
- Posibilidad de detectar si el nuevo prompt del usuario es:
  - Una nueva consulta (si cambia de tema)
  - Una ampliación/refinamiento (si es una referencia anafórica como “y si vamos con niños”)
- Este análisis puede realizarse en el `PreAnalyst` o en una nueva función llamada `FollowUpInterpreter`

---

## Beneficio

- Orquix se convierte en un verdadero asistente conversacional iterativo
- Se reduce la fricción para el usuario
- Se maximiza la reutilización del conocimiento ya generado
