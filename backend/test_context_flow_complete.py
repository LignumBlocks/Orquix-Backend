#!/usr/bin/env python3
"""
Script de prueba para el flujo completo de construcción de contexto.
Verifica que el context_builder genere automáticamente preguntas sugeridas.
"""

import asyncio
import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.context_builder import context_builder_service
from app.models.context_session import ContextMessage
from datetime import datetime

async def test_context_flow():
    """Prueba el flujo completo de construcción de contexto."""
    
    print("🧪 Iniciando prueba del flujo de construcción de contexto\n")
    
    # Simular una conversación de construcción de contexto
    conversation_history = []
    accumulated_context = ""
    
    # Lista de mensajes de prueba
    test_messages = [
        "Quiero construir un sistema de energía solar para mi casa",
        "Tengo una casa de 150 metros cuadrados en Medellín",
        "Mi consumo promedio es de 300 kWh al mes",
        "Tengo un presupuesto de 15 millones de pesos",
        "¿Qué más necesitas saber?"
    ]
    
    for i, user_message in enumerate(test_messages, 1):
        print(f"--- Mensaje {i} ---")
        print(f"👤 Usuario: {user_message}")
        
        # Procesar mensaje
        response = await context_builder_service.process_user_message(
            user_message=user_message,
            conversation_history=conversation_history,
            current_context=accumulated_context
        )
        
        print(f"🤖 IA: {response.ai_response}")
        print(f"📊 Tipo: {response.message_type}")
        print(f"🧩 Elementos de contexto: {response.context_elements_count}")
        
        if response.suggested_final_question:
            print(f"🎯 Pregunta sugerida: {response.suggested_final_question}")
        
        print(f"📝 Contexto acumulado:\n{response.accumulated_context}")
        
        # Actualizar historial
        conversation_history.extend([
            ContextMessage(
                role="user",
                content=user_message,
                timestamp=datetime.utcnow(),
                message_type=response.message_type
            ),
            ContextMessage(
                role="assistant", 
                content=response.ai_response,
                timestamp=datetime.utcnow(),
                message_type=response.message_type
            )
        ])
        
        accumulated_context = response.accumulated_context
        
        print("\n" + "="*60 + "\n")
        
        # Si el contexto está listo, simular finalización
        if response.message_type == "ready" and response.suggested_final_question:
            print(f"✅ Contexto completo! Enviando pregunta a IAs principales:")
            print(f"❓ Pregunta final: {response.suggested_final_question}")
            print(f"📋 Contexto: {accumulated_context}")
            break
    
    print("🎉 Prueba completada exitosamente!")

if __name__ == "__main__":
    asyncio.run(test_context_flow()) 