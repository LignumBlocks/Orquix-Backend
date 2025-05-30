# Orquix – Public API Endpoints (MVP)

All endpoints are under `/api` and require a **Bearer JWT**.

| Method | Path | Purpose |
|--------|------|---------|
| GET | /auth/session | Validate token & return profile |
| POST | /projects | Create project |
| GET | /projects | List projects |
| GET | /projects/{{projectId}} | Project details |
| POST | /projects/{{projectId}}/query | Run orchestration loop |
| GET | /projects/{{projectId}}/sessions | List sessions |
| POST | /feedback | Submit feedback |

## Example – POST /projects/{{projectId}}/query

```json
{
  "question": "How can we reduce inference latency?",
  "moderator_params": {
    "personality": "Analytical",
    "temperature": 0.6
  }
}
```

SSE response streams chunks:

```json
{ "type": "chunk", "data": "partial text" }
{ "type": "done", "synthesis_id": "uuid" }
```
