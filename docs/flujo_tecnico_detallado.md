Flujo Técnico Detallado
get_context_for_query() - Búsqueda Inteligente
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

 save_interaction_background() - Almacenamiento Automático
 Usuario: "Dame un ejemplo práctico de deep learning"
┌─────────────────────┐
│ CONTEXTO COMBINADO: │
│ 1. ML definición    │ ← Similitud: 0.7
│ 2. Redes neuronales │ ← Similitud: 0.9  
│ 3. Otros temas...   │ ← Similitud: 0.6
└─────────────────────┘
           ↓
  [Contexto Enriquecido] 
  "ML es... Las redes neuronales..."
           ↓
    [AI con contexto completo]

Tipos de Contexto Almacenados
async def get_context_for_query(query: str, project_id: UUID):
    # 1. Genera embedding de la nueva pregunta
    query_embedding = await generate_embedding(query)
    
    # 2. Busca chunks similares con pgvector (cosine similarity)
    chunks = await find_similar_chunks(
        query_embedding,
        project_id=project_id,
        top_k=10,
        similarity_threshold=0.3  # 30% mínimo de similitud
    )
    
    # 3. Combina contexto relevante respetando límites de tokens
    context_block = await generate_context_block(
        max_tokens=4000,
        chunks_used=chunks
    )
    
    return context_block.context_text  # Enviado a las IAs