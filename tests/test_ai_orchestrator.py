import pytest
import asyncio
from app.services.ai_orchestrator import AIOrchestrator, AIOrchestrationStrategy
from app.schemas.ai_response import AIRequest, AIProviderEnum, AIResponseStatus
from app.core.config import settings

async def test_orchestrator_initialization():
    """Prueba la inicialización del orquestador"""
    print("\n🤖 Probando inicialización del orquestador...")
    
    orchestrator = AIOrchestrator()
    
    available_providers = orchestrator.get_available_providers()
    print(f"   📋 Proveedores disponibles: {available_providers}")
    
    assert isinstance(available_providers, list)
    
    # Verificar que al menos OpenAI esté disponible (ya que tenemos la API key)
    if settings.OPENAI_API_KEY:
        assert AIProviderEnum.OPENAI in available_providers
        print("   ✅ OpenAI disponible")
    
    await orchestrator.close()
    return True

async def test_single_openai_request():
    """Prueba una solicitud simple a OpenAI"""
    print("\n🎯 Probando solicitud individual a OpenAI...")
    
    orchestrator = AIOrchestrator()
    
    if AIProviderEnum.OPENAI not in orchestrator.get_available_providers():
        print("   ⚠️ OpenAI no disponible, saltando prueba")
        return True
    
    request = AIRequest(
        prompt="Explica en una oración qué es la inteligencia artificial.",
        max_tokens=50,
        temperature=0.7
    )
    
    response = await orchestrator.generate_single_response(
        request, 
        AIProviderEnum.OPENAI
    )
    
    print(f"   🤖 Proveedor: {response.ia_provider_name}")
    print(f"   📊 Estado: {response.status}")
    print(f"   ⏱️  Latencia: {response.latency_ms}ms")
    
    if response.status == AIResponseStatus.SUCCESS:
        print(f"   💬 Respuesta: {response.response_text}")
        print(f"   📈 Uso: {response.usage_info}")
        assert response.response_text is not None
        assert len(response.response_text) > 0
    else:
        print(f"   ❌ Error: {response.error_message}")
    
    await orchestrator.close()
    return True

async def test_fallback_strategy():
    """Prueba la estrategia de fallback"""
    print("\n🔄 Probando estrategia de fallback...")
    
    orchestrator = AIOrchestrator()
    
    available_providers = orchestrator.get_available_providers()
    if not available_providers:
        print("   ⚠️ No hay proveedores disponibles, saltando prueba")
        return True
    
    request = AIRequest(
        prompt="¿Cuál es la capital de España?",
        max_tokens=30,
        temperature=0.3
    )
    
    response = await orchestrator.orchestrate(
        request, 
        strategy=AIOrchestrationStrategy.FALLBACK
    )
    
    print(f"   🤖 Proveedor usado: {response.ia_provider_name}")
    print(f"   📊 Estado: {response.status}")
    print(f"   ⏱️  Latencia: {response.latency_ms}ms")
    
    if response.status == AIResponseStatus.SUCCESS:
        print(f"   💬 Respuesta: {response.response_text}")
        assert response.response_text is not None
    else:
        print(f"   ❌ Error: {response.error_message}")
    
    await orchestrator.close()
    return True

async def test_parallel_strategy():
    """Prueba la estrategia paralela (solo si hay múltiples proveedores)"""
    print("\n⚡ Probando estrategia paralela...")
    
    orchestrator = AIOrchestrator()
    
    available_providers = orchestrator.get_available_providers()
    if len(available_providers) < 1:
        print("   ⚠️ Se necesita al menos un proveedor para esta prueba")
        return True
    
    request = AIRequest(
        prompt="Di 'Hola' en español.",
        max_tokens=10,
        temperature=0.1
    )
    
    responses = await orchestrator.orchestrate(
        request, 
        strategy=AIOrchestrationStrategy.PARALLEL
    )
    
    print(f"   📊 Número de respuestas: {len(responses)}")
    
    for i, response in enumerate(responses, 1):
        print(f"   🤖 Respuesta #{i}:")
        print(f"      → Proveedor: {response.ia_provider_name}")
        print(f"      → Estado: {response.status}")
        print(f"      → Latencia: {response.latency_ms}ms")
        
        if response.status == AIResponseStatus.SUCCESS:
            print(f"      → Texto: {response.response_text}")
        else:
            print(f"      → Error: {response.error_message}")
    
    await orchestrator.close()
    return True

if __name__ == "__main__":
    async def run_all_tests():
        tests = [
            test_orchestrator_initialization(),
            test_single_openai_request(),
            test_fallback_strategy(),
            test_parallel_strategy()
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Test {i+1} falló: {result}")
            elif result:
                success_count += 1
                print(f"✅ Test {i+1} exitoso")
            else:
                print(f"❌ Test {i+1} falló")
        
        print(f"\n🎯 RESULTADO: {success_count}/{len(tests)} tests exitosos")
        return success_count == len(tests)
    
    result = asyncio.run(run_all_tests())
    if result:
        print("🎉 Todos los tests del orquestador pasaron!")
    else:
        print("💥 Algunos tests fallaron") 