# Context Manager – Design

1. **Chunk** text (paragraphs, 20 % overlap)  
2. **Embed** using `sentence-transformers/all-MiniLM-L6-v2` (384‑d)  
3. **Store** in `context_chunks` with metadata  
4. **Retrieve** top‑k by cosine similarity (pgvector)

Token cap for combined context: **3000 tokens**.
