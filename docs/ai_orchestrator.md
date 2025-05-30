# AI Orchestrator – Design

Fixed providers:

| ID | Model |
|----|-------|
| openai_gpt4o_mini | GPT‑4o‑mini |
| anthropic_claude3_haiku | Claude 3 Haiku |

Async fan‑out via `httpx.AsyncClient` with 25 s timeout and 2 retries.
