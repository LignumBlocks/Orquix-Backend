# Incorporación de Historial Conversacional Corta en Orquix

## 🎯 Problema

En interacciones multi-turno, los usuarios pueden usar frases con referencias implícitas como:

> "Dame los últimos 4"

Estas frases **no tienen suficiente contenido semántico por sí solas** para ser interpretadas correctamente por un sistema que depende de búsqueda vectorial (`pgvector`). El resultado: el sistema **no encuentra nada relevante**, porque no hay coincidencias directas con “los últimos 4”.

---

## ✅ Solución: Historial Conversacional Reciente

Antes de enviar una nueva pregunta a las IAs orquestadas, el sistema debe **reconstruir un bloque textual con las interacciones anteriores más recientes** (user + moderador).

### Ejemplo

Supón el historial reciente fue:

```
Usuario: Hazme un itinerario de 4 días por Miami
Moderador: Día 1: ..., Día 2: ..., Día 3: ..., Día 4: ...
Usuario: Dame los últimos 4
```

En lugar de enviar solo:

```
Dame los últimos 4
```

Debemos enviar:

```
Historial reciente:
Usuario: Hazme un itinerario de 4 días por Miami
Moderador: Día 1: ..., Día 2: ...
---

Nueva pregunta: Dame los últimos 4
```

Esto proporciona el contexto necesario para que tanto el **Gestor de Contexto** como las **IAs** puedan interpretar correctamente la intención.

---

## ⚙️ Cómo se implementa

1. En el `ContextManager`, al recibir una nueva consulta:
2. Recuperar los últimos N `interaction_events` del mismo `project_id` y `user_id`:
   ```sql
   SELECT user_prompt_text, moderated_synthesis
   FROM interaction_events
   WHERE project_id = ? AND user_id = ?
   ORDER BY created_at DESC
   LIMIT 3
   ```

3. Formatear los resultados:
   ```
   Usuario: ...
   Moderador: ...
   ```

4. Concatenar el historial con el prompt actual:
   ```python
   enriched_prompt = historial + "\n---\nNueva pregunta: " + user_prompt
   ```

5. Este `enriched_prompt` se usa:
   - Para generar el embedding de búsqueda en `pgvector`
   - Y/o se pasa directamente a las IAs

---

## 🧠 Ventajas

| Ventaja | Beneficio |
|--------|-----------|
| No requiere estructura nueva en la base de datos | Usa `interaction_events` |
| Compatible con el MVP actual | Se puede integrar de inmediato |
| Mejora comprensión de preguntas anafóricas | “eso”, “los 4 últimos”, “lo que me diste” |
| Escalable | Puedes controlar cuántos eventos usar (por tokens, tiempo o cantidad) |

---

## 🛠️ Recomendación de implementación

Agregar esta funcionalidad como parte de la **Tarea 1.3 (Context Block)** o crear una nueva:

> **Tarea 1.4: Incorporación de Memoria Conversacional Corta**

---

## 📌 Notas

- Este historial no se guarda como contexto vectorial (no son chunks), sino como bloque textual dinámico.
- Se recomienda usar `created_at DESC` para priorizar lo más reciente.
- Puedes controlar el tamaño máximo por cantidad o tokens.

