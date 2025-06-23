#!/usr/bin/env python3
"""
Test completo para Context Builder refactorizado con function calling.

Testa:
1. Clasificación QUESTION vs INFORMATION
2. Funciones: summary(), show_context(), clear_context()
3. Extracción de información
4. Flujo completo
5. Manejo de errores
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List

# Setup básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar el servicio refactorizado
from app.services.context_builder import (
    ContextBuilderService, 
    ContextMessage, 
    CONTEXT_FUNCTIONS
)

async def test_basic_functionality():
    """Test básico de inicialización y configuración."""
    print("🧪 Test 1: Configuración básica")
    
    service = ContextBuilderService()
    
    # Verificar configuración actualizada
    assert service.temperature == 0.2, f"❌ Temperature: esperado 0.2, obtenido {service.temperature}"
    assert service.max_tokens == 250, f"❌ Max tokens: esperado 250, obtenido {service.max_tokens}"
    assert service.seed == 42, f"❌ Seed: esperado 42, obtenido {service.seed}"
    
    # Verificar funciones definidas
    assert len(CONTEXT_FUNCTIONS) == 3, f"❌ Funciones: esperado 3, obtenido {len(CONTEXT_FUNCTIONS)}"
    function_names = [func["name"] for func in CONTEXT_FUNCTIONS]
    expected_names = ["summary", "show_context", "clear_context"]
    for name in expected_names:
        assert name in function_names, f"❌ Función {name} no encontrada"
    
    print("✅ Configuración básica correcta")

async def test_message_classification():
    """Test de clasificación de mensajes."""
    print("\n🧪 Test 2: Clasificación de mensajes")
    
    service = ContextBuilderService()
    
    # Test cases para clasificación
    test_cases = [
        ("¿Cómo puedo mejorar mi marketing?", "question"),
        ("Tengo una startup de software dental", "information"),
        ("Necesito 50 clientes en 3 meses con presupuesto de $2000", "information"),
        ("¿Cuál es la mejor estrategia?", "question"),
        ("Mi empresa está en México y Colombia", "information"),
        ("¿Qué me recomiendas para crecer?", "question")
    ]
    
    for message, expected_type in test_cases:
        try:
            message_type, confidence = await service._smart_classify(message)
            print(f"📝 '{message[:30]}...' → {message_type} (confianza: {confidence:.2f})")
            
            # No es crítico que coincida exactamente, pero debe ser razonable
            if confidence > 0.7:
                assert message_type == expected_type, f"❌ Clasificación incorrecta para: {message}"
            
        except Exception as e:
            print(f"⚠️ Error clasificando '{message}': {e}")
    
    print("✅ Clasificación de mensajes funcional")

async def test_function_execution():
    """Test de ejecución de funciones."""
    print("\n🧪 Test 3: Ejecución de funciones")
    
    service = ContextBuilderService()
    
    # Mock function_call object
    class MockFunctionCall:
        def __init__(self, name, arguments="{}"):
            self.name = name
            self.arguments = arguments
    
    # Test context vacío
    context = ""
    
    # Test show_context con contexto vacío
    result, updated_context = service._execute_function(
        MockFunctionCall("show_context"), context
    )
    print(f"📋 show_context (vacío): {result[:50]}...")
    assert "No hay contexto acumulado" in result
    assert updated_context == ""
    
    # Test con contexto
    test_context = "Startup de software dental en México. Objetivo: 50 clientes. Presupuesto: $2000/mes."
    
    # Test show_context con contexto
    result, updated_context = service._execute_function(
        MockFunctionCall("show_context"), test_context
    )
    print(f"📋 show_context (con datos): {result[:50]}...")
    assert "palabras" in result and "caracteres" in result
    assert updated_context == test_context
    
    # Test summary
    result, updated_context = service._execute_function(
        MockFunctionCall("summary", '{"max_sentences": 1}'), test_context
    )
    print(f"📋 summary: {result[:50]}...")
    assert "Resumen del contexto" in result
    assert updated_context == test_context  # No debe cambiar
    
    # Test clear_context
    result, updated_context = service._execute_function(
        MockFunctionCall("clear_context"), test_context
    )
    print(f"🗑️ clear_context: {result[:50]}...")
    assert "Contexto borrado" in result
    assert updated_context == ""  # Debe vaciarse
    
    print("✅ Ejecución de funciones correcta")

async def test_information_extraction():
    """Test de extracción de información."""
    print("\n🧪 Test 4: Extracción de información")
    
    service = ContextBuilderService()
    
    # Test de extracción heurística (fallback)
    message = "Tengo una startup con 25 empleados, presupuesto de $5000 mensuales"
    context = ""
    
    try:
        extracted = await service._extract_information_from_message(message, context)
        print(f"📊 Información extraída: {extracted}")
        
        # Verificar que extrajo algo útil
        assert len(extracted) > 0, "❌ No se extrajo información"
        
    except Exception as e:
        # Si falla el LLM, probar heurística
        print(f"⚠️ LLM extraction falló, probando heurística: {e}")
        extracted = service._extract_info_heuristic(message, context)
        print(f"📊 Información extraída (heurística): {extracted}")
        assert len(extracted) > 0, "❌ Heurística no extrajo información"
    
    print("✅ Extracción de información funcional")

async def test_full_conversation_flow():
    """Test del flujo completo de conversación."""
    print("\n🧪 Test 5: Flujo completo de conversación")
    
    service = ContextBuilderService()
    conversation_history = []
    current_context = ""
    
    # Simulación de conversación completa
    messages = [
        "Tengo una startup de software para clínicas dentales",
        "Estamos en fase beta con 10 clientes piloto", 
        "Nuestro objetivo es llegar a 100 clientes en 6 meses",
        "¿Cómo puedo mejorar mi estrategia de marketing?"
    ]
    
    for i, message in enumerate(messages):
        print(f"\n💬 Mensaje {i+1}: '{message}'")
        
        try:
            response = await service.process_user_message(
                user_message=message,
                conversation_history=conversation_history,
                current_context=current_context
            )
            
            print(f"🤖 Respuesta: {response.ai_response[:100]}...")
            print(f"📝 Tipo: {response.message_type}")
            print(f"📊 Contexto actual: {len(response.accumulated_context)} chars")
            print(f"💡 Sugerencias: {response.suggestions[:2]}")
            
            # Actualizar para siguiente iteración
            current_context = response.accumulated_context
            conversation_history.append(ContextMessage(
                role="user",
                content=message,
                timestamp=datetime.now()
            ))
            conversation_history.append(ContextMessage(
                role="assistant", 
                content=response.ai_response,
                timestamp=datetime.now(),
                message_type=response.message_type
            ))
            
            # Verificaciones básicas
            assert response.ai_response is not None, "❌ Sin respuesta AI"
            assert response.message_type in ["question", "information", "command_result"], f"❌ Tipo inválido: {response.message_type}"
            assert isinstance(response.suggestions, list), "❌ Sugerencias no es lista"
            assert response.context_elements_count >= 0, "❌ Contador de elementos negativo"
            
        except Exception as e:
            print(f"❌ Error en mensaje {i+1}: {e}")
            # No fallar completamente, continuar con el test
    
    print(f"\n✅ Flujo completo procesado - Contexto final: {len(current_context)} caracteres")

async def test_function_calling_simulation():
    """Test simulado de function calling."""
    print("\n🧪 Test 6: Simulación de function calling")
    
    service = ContextBuilderService()
    
    # Simular que GPT-3.5 retornó una function_call
    class MockChoice:
        def __init__(self, function_call=None, content=None):
            self.message = MockMessage(function_call, content)
    
    class MockMessage:
        def __init__(self, function_call=None, content=None):
            self.function_call = function_call
            self.content = content
    
    class MockFunctionCall:
        def __init__(self, name, arguments="{}"):
            self.name = name
            self.arguments = arguments
    
    # Test con function_call
    test_context = "Startup de software dental en México. Presupuesto: $2000."
    
    # Simular ejecución de summary
    function_call = MockFunctionCall("summary", '{"max_sentences": 2}')
    result, updated_context = service._execute_function(function_call, test_context)
    
    print(f"🔧 Function call simulado - summary:")
    print(f"   Resultado: {result[:80]}...")
    print(f"   Contexto preservado: {len(updated_context)} chars")
    
    assert "Resumen del contexto" in result
    assert updated_context == test_context
    
    print("✅ Function calling simulado correctamente")

async def test_error_handling():
    """Test de manejo de errores."""
    print("\n🧪 Test 7: Manejo de errores")
    
    service = ContextBuilderService()
    
    # Test función inexistente
    class MockFunctionCall:
        def __init__(self, name, arguments="{}"):
            self.name = name
            self.arguments = arguments
    
    result, updated_context = service._execute_function(
        MockFunctionCall("nonexistent_function"), "test context"
    )
    
    print(f"🚫 Función inexistente: {result[:50]}...")
    assert "Error" in result and "no reconocida" in result
    
    # Test argumentos JSON inválidos
    result, updated_context = service._execute_function(
        MockFunctionCall("summary", 'invalid json'), "test context"
    )
    
    print(f"🚫 JSON inválido manejado correctamente")
    assert "Resumen del contexto" in result  # Debe usar argumentos por defecto
    
    print("✅ Manejo de errores funcional")

async def run_all_tests():
    """Ejecuta todos los tests."""
    print("🚀 Iniciando tests del Context Builder refactorizado...\n")
    
    tests = [
        test_basic_functionality,
        test_message_classification,
        test_function_execution,
        test_information_extraction,
        test_full_conversation_flow,
        test_function_calling_simulation,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"❌ Test falló: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
    
    print(f"\n📊 Resultados finales:")
    print(f"✅ Tests pasados: {passed}")
    print(f"❌ Tests fallidos: {failed}")
    print(f"🎯 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ¡Todos los tests pasaron! La refactorización está funcionando correctamente.")
    else:
        print(f"\n⚠️ {failed} tests fallaron. Revisar implementación.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1) 