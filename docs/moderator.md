# Moderator – Design

Pipeline:

1. Extract key sentences from each answer (GPT‑3.5‑Turbo).  
2. Merge & deduplicate.  
3. Detect blatant factual clashes.  
4. Generate ≤ 250‑word synthesis highlighting conflicts.

Returns: synthesis text + notes.
