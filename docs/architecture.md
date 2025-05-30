# Orquix – Backend Architecture

## Services

| Service | Purpose | Tech |
|---------|---------|------|
| API Gateway | Exposes REST + SSE, auth, rate‑limit, orchestrates sub‑services | FastAPI, Uvicorn |
| Context Manager | Embedding generation & semantic search | Python, sentence‑transformers, pgvector |
| AI Orchestrator | Builds prompts and issues async calls to LLMs | Python, httpx, asyncio |
| Moderator | Synthesises multiple answers into one | GPT‑3.5‑Turbo |
| Workers | Background jobs (file ingestion, backups) | RQ, Redis |

All modules live in one FastAPI monorepo for MVP simplicity.

### Deployment

* Railway container (API + services)  
* Railway PostgreSQL (pgvector)  
* Railway Redis (rate‑limit, RQ)  
* Supabase Storage (context files)

TLS termination at Railway.  
