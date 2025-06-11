#!/usr/bin/env python3
"""
Script de prueba específico para el caso de Cristóbal Colón.
"""

import asyncio
import os
import sys

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.context_manager import ContextManager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings

async def test_cristobal_case():
    """Prueba específica del caso de Cristóbal Colón"""
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session = AsyncSession(engine)
    
    context_manager = ContextManager(session)
    
    # Simular el caso real del usuario
    queries = [
        ("¿Cuál es la tierra más hermosa que ojos humanos hayan visto?", "Primera consulta independiente"),
        ("Tiene esto algo que ver con Cristóbal Colón", "Segunda consulta con referencia implícita 'esto'")
    ]
    
    print("🧭 Caso Cristóbal Colón - Análisis de consultas:")
    print("=" * 60)
    
    for query, description in queries:
        needs_history = context_manager._query_needs_history(query)
        status = "🔍 NECESITA HISTORIAL" if needs_history else "✅ INDEPENDIENTE"
        
        print(f"\n{status}")
        print(f"Query: '{query}'")
        print(f"Descripción: {description}")
        print(f"Detección: {needs_history}")
        
        # Mostrar patrones detectados
        query_lower = query.lower().strip()
        patterns_found = []
        
        implicit_patterns = [
            "últimos", "primeros", "anteriores", "previos",
            "eso", "esto", "esos", "estas", "aquello", "lo que",
            "el que", "la que", "los que", "las que",
            "antes", "después", "luego", "ahora", "ya",
            "mejora", "cambia", "modifica", "ajusta", "corrige",
            "amplía", "resume", "explica", "detalla",
            "los 4", "las 5", "los 3", "dame 2",
            "mejor", "peor", "similar", "parecido", "como",
            "resultado", "respuesta", "lo anterior", "arriba"
        ]
        
        for pattern in implicit_patterns:
            if pattern in query_lower:
                patterns_found.append(pattern)
        
        if patterns_found:
            print(f"Patrones encontrados: {patterns_found}")
        
        # Verificar si es query corta
        words = query.split()
        if len(words) <= 3:
            interrogative_words = ["qué", "que", "cómo", "como", "cuándo", "cuando", "dónde", "donde", "por", "para", "quién", "quien"]
            first_word = words[0].lower().strip("¿?")
            is_interrogative = first_word in interrogative_words
            print(f"Query corta ({len(words)} palabras): Primera palabra '{first_word}' {'ES' if is_interrogative else 'NO ES'} interrogativa")
    
    await session.close()

async def test_enrichment_simulation():
    """Simula cómo se vería el enriquecimiento"""
    
    print("\n" + "=" * 60)
    print("🔄 Simulación de enriquecimiento:")
    print("=" * 60)
    
    # Historial simulado de la conversación
    mock_history = [
        {
            "user_prompt": "¿Cuál es la tierra más hermosa que ojos humanos hayan visto?",
            "moderator_response": "Basándome en las respuestas de múltiples IAs, las tierras más hermosas incluyen:\n\n1. **Santorini, Grecia** - Con sus casas blancas y mar azul\n2. **Maldivas** - Aguas cristalinas y atolones\n3. **Alpes Suizos** - Paisajes montañosos espectaculares\n4. **Jamaica** - Playas de arena blanca\n5. **Patagonia** - Paisajes vírgenes y glaciares",
            "timestamp": "2024-01-20T15:30:00"
        }
    ]
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session = AsyncSession(engine)
    context_manager = ContextManager(session)
    
    # Formatear el historial
    formatted_history = context_manager.format_conversation_history(mock_history, max_total_tokens=600)
    
    # Query original
    original_query = "Tiene esto algo que ver con Cristóbal Colón"
    
    # Query enriquecida
    enriched_query = f"{formatted_history}Nueva pregunta: {original_query}"
    
    print("QUERY ORIGINAL:")
    print(f"'{original_query}'")
    print("\nQUERY ENRIQUECIDA:")
    print("-" * 40)
    print(enriched_query)
    print("-" * 40)
    
    print("\n💡 Con este contexto, las IAs podrían responder:")
    print("   'Sí, la frase sobre \"la tierra más hermosa que ojos humanos hayan visto\"")
    print("   es atribuida a Cristóbal Colón cuando describió Cuba en sus diarios...")
    
    await session.close()

async def main():
    """Función principal"""
    print("🧭 Análisis del caso Cristóbal Colón\n")
    
    try:
        await test_cristobal_case()
        await test_enrichment_simulation()
        
        print("\n✅ Análisis completado!")
        
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 