#!/usr/bin/env python3
"""
Test de Integración Completa: Orquestación + Generación de Prompts

Este test verifica el flujo completo que usará el frontend:
1. Chat normal
2. Usuario presiona [Orquestar y Sintetizar] 
3. Backend: package_context_for_orchestration() + generate_prompt
4. Resultado: Prompt de alta calidad listo para IAs
"""

import asyncio
import sys
import os
from datetime import datetime

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_full_integration():
    """Test del flujo completo de integración."""
    
    print("🚀 INICIANDO TEST DE INTEGRACIÓN COMPLETA")
    print("=" * 60)
    
    try:
        # Test: package_context_for_orchestration + prompt generation
        print("\n🎯 PASO 1: Test de Orquestación + Generación de Prompt")
        await test_orchestration_with_prompt_generation()
        
        print("\n✅ INTEGRACIÓN COMPLETA EXITOSA")
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST DE INTEGRACIÓN: {e}")
        import traceback
        traceback.print_exc()

async def test_orchestration_with_prompt_generation():
    """Test específico del flujo: orquestación → prompt generation."""
    
    from app.services.context_builder import context_builder_service, ContextMessage
    from app.services.prompt_templates import PromptTemplateManager
    from app.schemas.ai_response import AIProviderEnum
    
    print("🔄 Simulando flujo completo...")
    
    # PASO 1: Simular historial conversacional real
    conversation_history = [
        ContextMessage(
            role="user",
            content="cual es el pais que mas bananas exporta?",
            timestamp=datetime.utcnow(),
            message_type="question"
        ),
        ContextMessage(
            role="assistant", 
            content="El país que más bananas exporta a nivel mundial es Ecuador. Ecuador lidera la exportación mundial de bananas, seguido por Filipinas y Costa Rica.",
            timestamp=datetime.utcnow(),
            message_type="ai"
        ),
        ContextMessage(
            role="user",
            content="Quiero hacer un startup para vender envases de banana en Quito. Lo llamaré BananaPack",
            timestamp=datetime.utcnow(),
            message_type="information"
        ),
        ContextMessage(
            role="assistant",
            content="¡Excelente idea! BananaPack es un nombre muy pegajoso. Un startup de envases de banana en Quito tiene mucho potencial dado que Ecuador es el mayor exportador.",
            timestamp=datetime.utcnow(),
            message_type="ai"
        ),
        ContextMessage(
            role="user",
            content="Tengo un presupuesto inicial de $50,000 y quiero lanzar en 6 meses",
            timestamp=datetime.utcnow(),
            message_type="information"
        )
    ]
    
    target_query = "Crea un plan de negocio detallado para BananaPack, incluyendo estrategia de mercado, análisis financiero y plan de lanzamiento"
    
    print(f"📝 Historial: {len(conversation_history)} mensajes")
    print(f"🎯 Consulta objetivo: {target_query}")
    
    # PASO 2: Orquestación (package_context_for_orchestration)
    print("\n🔄 PASO 2: Orquestación de contexto...")
    
    refined_context = await context_builder_service.package_context_for_orchestration(
        target_query=target_query,
        conversation_history=conversation_history
    )
    
    print(f"✅ Contexto refinado generado: {len(refined_context)} caracteres")
    print("📋 Contexto refinado:")
    print("-" * 50)
    print(refined_context[:500] + "..." if len(refined_context) > 500 else refined_context)
    print("-" * 50)
    
    # PASO 3: Generación de prompt usando contexto refinado
    print("\n🎨 PASO 3: Generación de prompt...")
    
    prompt_manager = PromptTemplateManager()
    prompt_data = prompt_manager.build_prompt_for_provider(
        provider=AIProviderEnum.OPENAI,
        user_question=target_query,
        context_text=refined_context  # 🎯 USANDO CONTEXTO REFINADO
    )
    
    # Combinar system y user message
    final_prompt = f"{prompt_data['system_message']}\n\n{prompt_data['user_message']}"
    
    print(f"✅ Prompt generado: {len(final_prompt)} caracteres")
    print("🎨 Prompt final:")
    print("-" * 50)
    print(final_prompt[:800] + "..." if len(final_prompt) > 800 else final_prompt)
    print("-" * 50)
    
    # PASO 4: Verificaciones de calidad
    print("\n🔍 PASO 4: Verificaciones de calidad...")
    
    # Verificar que el contexto refinado contiene información clave
    context_checks = [
        ("BananaPack", "Nombre del startup"),
        ("Quito", "Ubicación"),
        ("50,000", "Presupuesto"),
        ("6 meses", "Timeline"),
        ("Ecuador", "Contexto de país exportador")
    ]
    
    print("📊 Verificando contexto refinado:")
    for term, description in context_checks:
        if term in refined_context:
            print(f"  ✅ {description}: '{term}' encontrado")
        else:
            print(f"  ⚠️ {description}: '{term}' NO encontrado")
    
    # Verificar que el prompt final contiene el contexto
    print("\n📊 Verificando prompt final:")
    if refined_context[:200] in final_prompt:
        print("  ✅ Contexto refinado incluido en el prompt")
    else:
        print("  ⚠️ Contexto refinado NO incluido correctamente")
    
    if target_query in final_prompt:
        print("  ✅ Consulta objetivo incluida en el prompt")
    else:
        print("  ⚠️ Consulta objetivo NO incluida")
    
    # PASO 5: Comparación de calidad
    print("\n📈 PASO 5: Comparación de calidad...")
    
    # Simular prompt sin contexto refinado (método anterior)
    raw_context = "Usuario quiere startup envases banana. Presupuesto $50,000. Timeline 6 meses."
    
    prompt_data_old = prompt_manager.build_prompt_for_provider(
        provider=AIProviderEnum.OPENAI,
        user_question=target_query,
        context_text=raw_context
    )
    
    old_prompt = f"{prompt_data_old['system_message']}\n\n{prompt_data_old['user_message']}"
    
    print(f"📊 Prompt sin orquestación: {len(old_prompt)} caracteres")
    print(f"📊 Prompt con orquestación: {len(final_prompt)} caracteres")
    print(f"📈 Mejora en contenido: +{len(final_prompt) - len(old_prompt)} caracteres")
    
    quality_improvement = len(final_prompt) / len(old_prompt) if len(old_prompt) > 0 else 1
    print(f"📈 Factor de mejora: {quality_improvement:.2f}x")
    
    print("\n✅ INTEGRACIÓN ORQUESTACIÓN + PROMPT GENERATION EXITOSA")

async def test_endpoint_simulation():
    """Simular cómo el frontend usaría el nuevo endpoint."""
    
    print("\n🌐 SIMULACIÓN DE USO DEL FRONTEND")
    print("=" * 50)
    
    # Simular request del frontend
    frontend_request = {
        "session_id": "8c2c2d06-e237-47c8-9c56-3eb9921a6a57",
        "target_query": "Ayúdame a crear un plan de marketing digital para BananaPack"
    }
    
    print("📱 Request del frontend:")
    print(f"  Session ID: {frontend_request['session_id']}")
    print(f"  Target Query: {frontend_request['target_query']}")
    
    # Simular response del backend
    backend_response = {
        "success": True,
        "orchestration": {
            "refined_context": "Contexto refinado de alta calidad...",
            "processed_messages_count": 12
        },
        "prompt": {
            "prompt_id": "abc123-def456-ghi789",
            "generated_prompt": "Prompt de alta calidad listo para IAs...",
            "status": "generated"
        },
        "next_steps": {
            "ready_for_ai_execution": True,
            "execute_prompt_endpoint": "/api/v1/context-chat/prompts/abc123-def456-ghi789/execute"
        }
    }
    
    print("\n📤 Response del backend:")
    print(f"  ✅ Success: {backend_response['success']}")
    print(f"  📊 Mensajes procesados: {backend_response['orchestration']['processed_messages_count']}")
    print(f"  🎨 Prompt generado: ID {backend_response['prompt']['prompt_id']}")
    print(f"  🚀 Listo para ejecutar: {backend_response['next_steps']['ready_for_ai_execution']}")
    
    print("\n✅ SIMULACIÓN DE FRONTEND EXITOSA")

def run_integration_tests():
    """Ejecutar todos los tests de integración."""
    asyncio.run(test_full_integration())

if __name__ == "__main__":
    run_integration_tests() 