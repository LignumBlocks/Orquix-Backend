Contexto Acumulativo Inteligente
1. Primera Pregunta del Usuario
Usuario: "¿Qué es machine learning?"
┌─────────────────────┐
│ PROYECTO VACÍO      │ → No hay contexto previo
└─────────────────────┘
           ↓
    [AI Orchestrator]
           ↓
    [AI Moderator] → Síntesis: "Machine learning es..."
           ↓
 [ContextManager.process_and_store_text()]
           ↓
┌─────────────────────┐
│ NUEVO CONTEXTO:     │
│ - "Machine learning │
│   es el campo..."   │
│ - source_type:      │
│   "ai_synthesis"    │
└─────────────────────┘

2. Segunda Pregunta del Usuario
Usuario: "¿Cómo funcionan las redes neuronales?"
┌─────────────────────┐
│ CONTEXTO EXISTENTE: │
│ - Machine learning  │ ← Se encuentra con búsqueda vectorial
│   definición...     │
└─────────────────────┘
           ↓
  [Búsqueda Semántica] 
  similarity_score: 0.8
           ↓
    [AI Orchestrator] 
    (con contexto de ML)
           ↓
    [AI Moderator] → Síntesis: "Las redes neuronales, como parte del ML..."
           ↓
 [Nuevo contexto almacenado]

 3. Tercera Pregunta del Usuario
 Usuario: "¿Qué es machine learning?"
┌─────────────────────┐
│ PROYECTO VACÍO      │ → No hay contexto previo
└─────────────────────┘
           ↓
    [AI Orchestrator]
           ↓
    [AI Moderator] → Síntesis: "Machine learning es..."
           ↓
 [ContextManager.process_and_store_text()]
           ↓
┌─────────────────────┐
│ NUEVO CONTEXTO:     │
│ - "Machine learning │
│   es el campo..."   │
│ - source_type:      │
│   "ai_synthesis"    │
└─────────────────────┘
