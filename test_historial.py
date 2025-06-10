#!/usr/bin/env python3
"""
Script de prueba para la funcionalidad de historial conversacional.
"""

import asyncio
import os
import sys
from uuid import UUID

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.context_manager import ContextManager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings

async def test_history_detection():
    """Prueba la detección de queries que necesitan historial"""
    
    # Crear context manager mock
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session = AsyncSession(engine)
    
    context_manager = ContextManager(session)
    
    # Casos de prueba
    test_cases = [
        ("Dame los últimos 4", True, "Referencias numéricas implícitas"),
        ("¿Qué es Python?", False, "Pregunta independiente"),
        ("Mejora eso", True, "Referencia implícita con 'eso'"),
        ("Explica mejor lo anterior", True, "Referencia temporal implícita"),
        ("Hola", True, "Query muy corta"),
        ("¿Puedes crear un itinerario de 5 días por Madrid?", False, "Pregunta completa independiente"),
        ("Cambia el día 3", True, "Referencia implícita con modificación"),
        ("Resume", True, "Acción sobre contenido previo")
    ]
    
    print("🧠 Testando detección de queries que necesitan historial conversacional:")
    print("=" * 70)
    
    for query, expected, reason in test_cases:
        needs_history = context_manager._query_needs_history(query)
        status = "✅" if needs_history == expected else "❌"
        
        print(f"{status} '{query}'")
        print(f"   Esperado: {expected} | Detectado: {needs_history}")
        print(f"   Razón: {reason}")
        print()
    
    await session.close()

async def test_history_formatting():
    """Prueba el formateo del historial conversacional"""
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session = AsyncSession(engine)
    
    context_manager = ContextManager(session)
    
    # Historial simulado
    mock_history = [
        {
            "user_prompt": "Hazme un itinerario de 4 días por Miami",
            "moderator_response": "Aquí tienes un itinerario completo para 4 días en Miami:\n\nDía 1: South Beach y Ocean Drive...\nDía 2: Downtown Miami...",
            "timestamp": "2024-01-20T10:00:00"
        },
        {
            "user_prompt": "¿Qué restaurantes me recomiendas?",
            "moderator_response": "Te recomiendo estos restaurantes en Miami:\n1. Joe's Stone Crab\n2. Versailles Restaurant...",
            "timestamp": "2024-01-20T10:05:00"
        }
    ]
    
    formatted = context_manager.format_conversation_history(mock_history, max_total_tokens=800)
    
    print("📝 Historial formateado:")
    print("=" * 50)
    print(formatted)
    
    await session.close()

async def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas de historial conversacional...\n")
    
    try:
        await test_history_detection()
        print("\n" + "="*70 + "\n")
        await test_history_formatting()
        
        print("\n✅ Todas las pruebas completadas!")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 