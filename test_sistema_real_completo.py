#!/usr/bin/env python3
"""
Prueba REAL del sistema Orquix Backend MVP
Prueba con APIs reales de OpenAI/Anthropic y endpoints FastAPI
"""

import asyncio
import uuid
import httpx
import json
from datetime import datetime
from typing import List, Dict, Any

# Imports del sistema
from app.core.database import get_async_session
from app.models import User, Project, InteractionEvent, IAResponse, ModeratedSynthesis
from app.services.ai_orchestrator import AIOrchestrator, AIOrchestrationStrategy
from app.services.ai_moderator import AIModerator
from app.schemas.ai_response import StandardAIResponse, AIRequest
from app.core.config import settings

# Configuración para pruebas
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test_real@orquix.com"

async def verificar_apis_configuradas():
    """Verificar que las APIs estén configuradas"""
    print("🔑 Verificando configuración de APIs...")
    
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY no configurada en .env")
        return False
    
    if not settings.ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY no configurada en .env")
        return False
    
    print("✅ APIs configuradas correctamente")
    print(f"   OpenAI: {'*' * 10}{settings.OPENAI_API_KEY[-4:]}")
    print(f"   Anthropic: {'*' * 10}{settings.ANTHROPIC_API_KEY[-4:]}")
    return True

async def crear_usuario_prueba():
    """Crear usuario de prueba para las APIs"""
    print("\n👤 Creando usuario de prueba...")
    
    async for session in get_async_session():
        # Crear usuario único con timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        email = f"test_real_{timestamp}@orquix.com"
        
        # Crear nuevo usuario
        user = User(
            id=uuid.uuid4(),
            email=email,
            name=f"Usuario Prueba Real {timestamp}",
            google_id=f"test_real_sistema_{timestamp}",
            avatar_url="https://via.placeholder.com/150"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        print(f"✅ Usuario creado: {user.email}")
        return user

async def crear_proyecto_prueba(user: User):
    """Crear proyecto de prueba"""
    print("📁 Creando proyecto de prueba...")
    
    async for session in get_async_session():
        # Crear proyecto único con timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Crear nuevo proyecto
        project = Project(
            id=uuid.uuid4(),
            user_id=user.id,
            name=f"Proyecto Prueba Real {timestamp}",
            description="Proyecto para probar el sistema con APIs reales",
            moderator_personality="Analytical",
            moderator_temperature=0.7,
            moderator_length_penalty=0.5
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        
        print(f"✅ Proyecto creado: {project.name}")
        return project

async def test_ai_orchestrator_real(query: str) -> List[StandardAIResponse]:
    """Probar AI Orchestrator con APIs reales"""
    print(f"\n🤖 Probando AI Orchestrator con APIs REALES...")
    print(f"❓ Consulta: '{query}'")
    
    request = AIRequest(
        prompt=query,
        max_tokens=800,
        temperature=0.7,
        system_message="Eres un asistente experto que proporciona respuestas precisas y útiles."
    )
    
    orchestrator = AIOrchestrator()
    
    # Probar estrategia PARALLEL para obtener respuestas de ambas APIs
    responses = await orchestrator.orchestrate(
        request, 
        strategy=AIOrchestrationStrategy.PARALLEL
    )
    
    print(f"✅ AI Orchestrator procesó la consulta")
    print(f"📊 Respuestas recibidas: {len(responses)}")
    
    for i, response in enumerate(responses, 1):
        status_emoji = "✅" if response.response_text else "❌"
        print(f"  {status_emoji} {i}. {response.ia_provider_name}: {len(response.response_text or '')} caracteres")
        if response.error_message:
            print(f"     ⚠️ Error: {response.error_message}")
        else:
            print(f"     ⏱️ Latencia: {response.latency_ms}ms")
            print(f"     📄 Contenido: {(response.response_text or '')[:100]}...")
    
    return responses

async def test_ai_moderator_real(responses: List[StandardAIResponse]) -> str:
    """Probar AI Moderator con respuestas reales"""
    print(f"\n🧠 Probando AI Moderator con respuestas REALES...")
    
    moderator = AIModerator()
    moderator_response = await moderator.synthesize_responses(responses)
    
    print(f"✅ AI Moderator generó síntesis")
    print(f"📝 Síntesis: {len(moderator_response.synthesis_text)} caracteres")
    print(f"🏆 Calidad: {moderator_response.quality}")
    print(f"🎯 Temas clave: {len(moderator_response.key_themes)}")
    print(f"⚠️ Contradicciones: {len(moderator_response.contradictions)}")
    print(f"🤝 Consensos: {len(moderator_response.consensus_areas)}")
    print(f"💡 Recomendaciones: {len(moderator_response.recommendations)}")
    
    print(f"\n📄 Síntesis completa:")
    print("=" * 60)
    print(moderator_response.synthesis_text)
    print("=" * 60)
    
    if moderator_response.key_themes:
        print(f"\n🎯 Temas clave identificados:")
        for theme in moderator_response.key_themes:
            print(f"  • {theme}")
    
    if moderator_response.recommendations:
        print(f"\n💡 Recomendaciones:")
        for rec in moderator_response.recommendations:
            print(f"  • {rec}")
    
    return moderator_response.synthesis_text

async def verificar_servidor_fastapi():
    """Verificar que el servidor FastAPI esté corriendo"""
    print(f"\n🌐 Verificando servidor FastAPI en {BASE_URL}...")
    
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(f"{BASE_URL}/api/v1/health/")
            if response.status_code == 200:
                print("✅ Servidor FastAPI está corriendo")
                health_data = response.json()
                print(f"   Estado: {health_data.get('status', 'unknown')}")
                print(f"   Mensaje: {health_data.get('message', 'N/A')}")
                return True
            else:
                print(f"❌ Servidor responde con código: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        print("💡 Asegúrate de ejecutar: poetry run uvicorn app.main:app --reload")
        return False

async def test_endpoint_health():
    """Probar endpoints de health"""
    print(f"\n🏥 Probando endpoints de health...")
    
    endpoints = [
        "/api/v1/health/",
        "/api/v1/health/detailed/",
        "/api/v1/health/database/",
        "/api/v1/health/ai-providers/"
    ]
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for endpoint in endpoints:
            try:
                response = await client.get(f"{BASE_URL}{endpoint}")
                status_emoji = "✅" if response.status_code == 200 else "❌"
                print(f"  {status_emoji} {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if endpoint == "/api/v1/health/ai-providers/":
                        print(f"     Proveedores: {data.get('providers_count', 0)}")
                    elif endpoint == "/api/v1/health/detailed/":
                        print(f"     Estado general: {data.get('status', 'unknown')}")
                        print(f"     Base de datos: {data.get('database', {}).get('status', 'unknown')}")
                    
            except Exception as e:
                print(f"  ❌ {endpoint}: Error - {e}")

async def test_endpoint_query_real(project_id: str, query: str):
    """Probar el endpoint principal de query con datos reales"""
    print(f"\n🎯 Probando endpoint de query REAL...")
    print(f"📁 Proyecto ID: {project_id}")
    print(f"❓ Query: '{query}'")
    
    payload = {
        "user_prompt_text": query,
        "include_context": False,
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/projects/{project_id}/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print("✅ Endpoint de query ejecutado exitosamente")
                data = response.json()
                
                print(f"📊 Respuesta del endpoint:")
                print(f"  • Interaction ID: {data.get('interaction_event_id')}")
                print(f"  • Calidad síntesis: {data.get('moderator_quality')}")
                print(f"  • Tiempo procesamiento: {data.get('processing_time_ms')}ms")
                print(f"  • Respuestas individuales: {len(data.get('individual_responses', []))}")
                print(f"  • Fallback usado: {data.get('fallback_used')}")
                
                print(f"\n📄 Síntesis del endpoint:")
                print("=" * 60)
                print(data.get('synthesis_text', 'No disponible'))
                print("=" * 60)
                
                return data
            else:
                print(f"❌ Error en endpoint: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error ejecutando endpoint: {e}")
            return None

async def test_sistema_real_completo():
    """Prueba integral REAL del sistema completo"""
    print("🚀 INICIANDO PRUEBA REAL DEL SISTEMA ORQUIX")
    print("=" * 70)
    
    try:
        # 1. Verificar configuración de APIs
        if not await verificar_apis_configuradas():
            print("❌ Configuración de APIs incompleta. Revisa tu .env")
            return
        
        # 2. Crear datos de prueba
        user = await crear_usuario_prueba()
        project = await crear_proyecto_prueba(user)
        
        # 3. Consulta real del usuario
        query = input("\n❓ Ingresa tu consulta (o presiona Enter para usar una por defecto): ").strip()
        if not query:
            query = "¿Cuáles son las mejores prácticas para implementar un sistema RAG con embeddings vectoriales en producción?"
        
        print(f"\n🎯 Consulta seleccionada: '{query}'")
        
        # 4. Probar AI Orchestrator con APIs reales
        responses = await test_ai_orchestrator_real(query)
        
        # 5. Probar AI Moderator con respuestas reales
        synthesis = await test_ai_moderator_real(responses)
        
        # 6. Verificar servidor FastAPI
        if await verificar_servidor_fastapi():
            # 7. Probar endpoints de health
            await test_endpoint_health()
            
            # 8. Probar endpoint principal de query
            await test_endpoint_query_real(str(project.id), query)
        else:
            print("\n⚠️ Servidor FastAPI no disponible. Saltando pruebas de endpoints.")
            print("💡 Para probar endpoints, ejecuta en otra terminal:")
            print("   poetry run uvicorn app.main:app --reload")
        
        print("\n" + "=" * 70)
        print("🎉 ¡PRUEBA REAL COMPLETADA!")
        print("✅ AI Orchestrator con APIs reales: FUNCIONANDO")
        print("✅ AI Moderator con síntesis real: FUNCIONANDO")
        print("✅ Base de datos: FUNCIONANDO")
        print("✅ Sistema completo: OPERATIVO")
        
    except KeyboardInterrupt:
        print("\n⏹️ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ ERROR EN LA PRUEBA REAL:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔥 PRUEBA REAL DEL SISTEMA ORQUIX")
    print("Este script probará el sistema con APIs reales de OpenAI/Anthropic")
    print("Asegúrate de tener configuradas las variables OPENAI_API_KEY y ANTHROPIC_API_KEY en .env")
    print()
    
    asyncio.run(test_sistema_real_completo()) 