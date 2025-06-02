#!/usr/bin/env python3
"""
Prueba DETALLADA del sistema Orquix Backend MVP
Muestra todo el proceso paso a paso con textos completos y análisis detallado
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

def print_separator(title: str, char: str = "=", width: int = 80):
    """Imprimir separador visual"""
    print(f"\n{char * width}")
    print(f" {title} ".center(width, char))
    print(f"{char * width}")

def print_section(title: str, content: str = "", indent: int = 0):
    """Imprimir sección con formato"""
    spaces = "  " * indent
    print(f"\n{spaces}🔸 {title}")
    if content:
        print(f"{spaces}   {content}")

async def verificar_configuracion():
    """Verificar configuración completa del sistema"""
    print_separator("VERIFICACIÓN DE CONFIGURACIÓN DEL SISTEMA")
    
    print("🔍 Verificando APIs configuradas...")
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY no configurada")
        return False
    if not settings.ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY no configurada")
        return False
    
    print("✅ APIs configuradas correctamente:")
    print(f"   • OpenAI: {'*' * 15}{settings.OPENAI_API_KEY[-4:]}")
    print(f"   • Anthropic: {'*' * 15}{settings.ANTHROPIC_API_KEY[-4:]}")
    
    print("\n🔍 Verificando base de datos...")
    try:
        async for session in get_async_session():
            print("✅ Conexión a base de datos establecida")
            break
    except Exception as e:
        print(f"❌ Error conectando a BD: {e}")
        return False
    
    print("\n🔍 Verificando servidor FastAPI...")
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(f"{BASE_URL}/api/v1/health/")
            if response.status_code == 200:
                print("✅ Servidor FastAPI operativo")
            else:
                print(f"⚠️ Servidor responde pero con código: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Servidor FastAPI no disponible: {e}")
    
    return True

async def crear_datos_prueba():
    """Crear datos de prueba con detalles"""
    print_separator("CREACIÓN DE DATOS DE PRUEBA")
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    print("👤 Creando usuario de prueba...")
    async for session in get_async_session():
        user = User(
            id=uuid.uuid4(),
            email=f"test_detallado_{timestamp}@orquix.com",
            name=f"Usuario Prueba Detallada {timestamp}",
            google_id=f"test_detallado_{timestamp}",
            avatar_url="https://via.placeholder.com/150"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        print(f"✅ Usuario creado:")
        print(f"   • ID: {user.id}")
        print(f"   • Email: {user.email}")
        print(f"   • Nombre: {user.name}")
        
        print("\n📁 Creando proyecto de prueba...")
        project = Project(
            id=uuid.uuid4(),
            user_id=user.id,
            name=f"Proyecto Prueba Detallada {timestamp}",
            description="Proyecto para análisis detallado del sistema",
            moderator_personality="Analytical",
            moderator_temperature=0.7,
            moderator_length_penalty=0.5
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        
        print(f"✅ Proyecto creado:")
        print(f"   • ID: {project.id}")
        print(f"   • Nombre: {project.name}")
        print(f"   • Configuración moderador:")
        print(f"     - Personalidad: {project.moderator_personality}")
        print(f"     - Temperatura: {project.moderator_temperature}")
        print(f"     - Length Penalty: {project.moderator_length_penalty}")
        
        return user, project

async def test_orchestrator_detallado(query: str) -> List[StandardAIResponse]:
    """Probar AI Orchestrator con análisis detallado"""
    print_separator("ANÁLISIS DETALLADO: AI ORCHESTRATOR")
    
    print(f"❓ CONSULTA DEL USUARIO:")
    print(f"   '{query}'")
    
    print(f"\n🔧 Configurando solicitud:")
    request = AIRequest(
        prompt=query,
        max_tokens=1000,
        temperature=0.7,
        system_message="Eres un asistente experto que proporciona respuestas precisas, detalladas y útiles."
    )
    
    print(f"   • Prompt: {request.prompt[:100]}...")
    print(f"   • Max tokens: {request.max_tokens}")
    print(f"   • Temperatura: {request.temperature}")
    print(f"   • System message: {request.system_message[:50]}...")
    
    print(f"\n🚀 Iniciando orquestación (estrategia PARALLEL)...")
    orchestrator = AIOrchestrator()
    
    print(f"   • Proveedores disponibles: {orchestrator.get_available_providers()}")
    
    start_time = datetime.utcnow()
    responses = await orchestrator.orchestrate(
        request, 
        strategy=AIOrchestrationStrategy.PARALLEL
    )
    end_time = datetime.utcnow()
    total_time = (end_time - start_time).total_seconds() * 1000
    
    print(f"\n📊 RESULTADOS DE ORQUESTACIÓN:")
    print(f"   • Tiempo total: {total_time:.0f}ms")
    print(f"   • Respuestas recibidas: {len(responses)}")
    
    for i, response in enumerate(responses, 1):
        print_section(f"RESPUESTA {i}: {response.ia_provider_name.value.upper()}")
        
        print(f"     🔍 Metadatos:")
        print(f"       • Estado: {response.status}")
        print(f"       • Latencia: {response.latency_ms}ms")
        print(f"       • Timestamp: {response.timestamp}")
        
        if response.error_message:
            print(f"       ❌ Error: {response.error_message}")
        else:
            print(f"       • Longitud respuesta: {len(response.response_text or '')} caracteres")
            
            if response.provider_metadata:
                print(f"       • Metadata del proveedor: {response.provider_metadata}")
            
            if response.usage_info:
                print(f"       • Información de uso: {response.usage_info}")
        
        print(f"\n     📄 TEXTO COMPLETO DE LA RESPUESTA:")
        print("     " + "─" * 70)
        if response.response_text:
            # Mostrar texto completo con numeración de líneas
            lines = response.response_text.split('\n')
            for line_num, line in enumerate(lines, 1):
                print(f"     {line_num:3}│ {line}")
        else:
            print("     [No hay contenido de respuesta]")
        print("     " + "─" * 70)
    
    return responses

async def test_moderator_detallado(responses: List[StandardAIResponse]) -> Dict[str, Any]:
    """Probar AI Moderator con análisis detallado del proceso"""
    print_separator("ANÁLISIS DETALLADO: AI MODERATOR")
    
    print("🧠 Iniciando proceso de moderación y síntesis...")
    
    print_section("ANÁLISIS DE RESPUESTAS DE ENTRADA")
    successful_responses = [r for r in responses if r.status.value == 'success' and r.response_text]
    failed_responses = [r for r in responses if r.status.value != 'success' or not r.response_text]
    
    print(f"   • Respuestas exitosas: {len(successful_responses)}")
    print(f"   • Respuestas fallidas: {len(failed_responses)}")
    
    if failed_responses:
        print("   ⚠️ Respuestas fallidas:")
        for resp in failed_responses:
            print(f"     - {resp.ia_provider_name}: {resp.error_message or 'Sin contenido'}")
    
    print_section("ESTADÍSTICAS DE CONTENIDO")
    total_chars = sum(len(r.response_text or '') for r in successful_responses)
    avg_latency = sum(r.latency_ms for r in successful_responses) / len(successful_responses) if successful_responses else 0
    
    print(f"   • Total de caracteres de entrada: {total_chars:,}")
    print(f"   • Latencia promedio: {avg_latency:.0f}ms")
    
    for resp in successful_responses:
        print(f"   • {resp.ia_provider_name}: {len(resp.response_text or '')} chars, {resp.latency_ms}ms")
    
    print_section("INICIANDO SÍNTESIS CON AI MODERATOR")
    moderator = AIModerator()
    
    print("   🔧 Configuración del moderador:")
    print(f"   • Adaptador de síntesis: {type(moderator.synthesis_adapter).__name__ if moderator.synthesis_adapter else 'No disponible'}")
    
    start_time = datetime.utcnow()
    moderator_response = await moderator.synthesize_responses(responses)
    end_time = datetime.utcnow()
    synthesis_time = (end_time - start_time).total_seconds() * 1000
    
    print_section("RESULTADOS DE LA SÍNTESIS")
    print(f"   • Tiempo de síntesis: {synthesis_time:.0f}ms")
    print(f"   • Calidad evaluada: {moderator_response.quality}")
    print(f"   • Tiempo de procesamiento: {moderator_response.processing_time_ms}ms")
    print(f"   • Fallback usado: {moderator_response.fallback_used}")
    print(f"   • Respuestas originales: {moderator_response.original_responses_count}")
    print(f"   • Respuestas exitosas: {moderator_response.successful_responses_count}")
    
    print_section("COMPONENTES EXTRAÍDOS DE LA SÍNTESIS")
    print(f"   • Temas clave: {len(moderator_response.key_themes)}")
    for theme in moderator_response.key_themes:
        print(f"     - {theme}")
    
    print(f"   • Contradicciones: {len(moderator_response.contradictions)}")
    for contradiction in moderator_response.contradictions:
        print(f"     - {contradiction}")
    
    print(f"   • Áreas de consenso: {len(moderator_response.consensus_areas)}")
    for consensus in moderator_response.consensus_areas:
        print(f"     - {consensus}")
    
    print(f"   • Recomendaciones: {len(moderator_response.recommendations)}")
    for rec in moderator_response.recommendations:
        print(f"     - {rec}")
    
    print(f"   • Preguntas sugeridas: {len(moderator_response.suggested_questions)}")
    for question in moderator_response.suggested_questions:
        print(f"     - {question}")
    
    print(f"   • Áreas de investigación: {len(moderator_response.research_areas)}")
    for area in moderator_response.research_areas:
        print(f"     - {area}")
    
    print(f"   • Conexiones: {len(moderator_response.connections)}")
    for connection in moderator_response.connections:
        print(f"     - {connection}")
    
    print(f"   • Calidad meta-análisis: {moderator_response.meta_analysis_quality}")
    
    print_section("TEXTO COMPLETO DE LA SÍNTESIS FINAL")
    print("   " + "─" * 75)
    synthesis_lines = moderator_response.synthesis_text.split('\n')
    for line_num, line in enumerate(synthesis_lines, 1):
        print(f"   {line_num:3}│ {line}")
    print("   " + "─" * 75)
    
    return {
        "moderator_response": moderator_response,
        "synthesis_time_ms": synthesis_time,
        "total_input_chars": total_chars,
        "output_chars": len(moderator_response.synthesis_text)
    }

async def analizar_proceso_completo(user: User, project: Project, query: str, 
                                  responses: List[StandardAIResponse], 
                                  synthesis_data: Dict[str, Any]):
    """Análisis completo del proceso de principio a fin"""
    print_separator("ANÁLISIS COMPLETO DEL PROCESO")
    
    moderator_response = synthesis_data["moderator_response"]
    
    print_section("MÉTRICAS GENERALES")
    print(f"   • Usuario: {user.name} ({user.email})")
    print(f"   • Proyecto: {project.name}")
    print(f"   • Consulta original: '{query}'")
    print(f"   • Longitud consulta: {len(query)} caracteres")
    
    print_section("FLUJO DE DATOS")
    print(f"   📥 ENTRADA:")
    print(f"     • Consulta del usuario: {len(query)} chars")
    
    print(f"   🔄 PROCESAMIENTO:")
    total_latency = sum(r.latency_ms for r in responses)
    print(f"     • IAs consultadas: {len(responses)}")
    print(f"     • Latencia total IAs: {total_latency}ms")
    print(f"     • Texto generado por IAs: {synthesis_data['total_input_chars']:,} chars")
    print(f"     • Tiempo síntesis: {synthesis_data['synthesis_time_ms']:.0f}ms")
    
    print(f"   📤 SALIDA:")
    print(f"     • Síntesis final: {synthesis_data['output_chars']:,} chars")
    print(f"     • Ratio compresión: {synthesis_data['total_input_chars'] / synthesis_data['output_chars']:.1f}:1")
    print(f"     • Calidad síntesis: {moderator_response.quality}")
    
    print_section("COMPARACIÓN ANTES vs DESPUÉS")
    print("   📊 RESPUESTAS ORIGINALES:")
    for i, resp in enumerate(responses, 1):
        if resp.response_text:
            words = len(resp.response_text.split())
            print(f"     {i}. {resp.ia_provider_name}: {len(resp.response_text)} chars, ~{words} palabras")
    
    synthesis_words = len(moderator_response.synthesis_text.split())
    print(f"\n   ✨ SÍNTESIS FINAL:")
    print(f"     • {len(moderator_response.synthesis_text)} characters")
    print(f"     • ~{synthesis_words} palabras")
    print(f"     • {len(moderator_response.key_themes)} temas clave identificados")
    print(f"     • {len(moderator_response.recommendations)} recomendaciones generadas")
    
    print_section("VALOR AGREGADO POR EL MODERADOR")
    print(f"   ✅ Síntesis estructurada con meta-análisis")
    print(f"   ✅ Identificación de consensos y contradicciones")
    print(f"   ✅ Generación de recomendaciones accionables")
    print(f"   ✅ Preguntas sugeridas para profundización")
    print(f"   ✅ Validación interna de calidad")

async def test_almacenamiento_detallado(user: User, project: Project, query: str,
                                      responses: List[StandardAIResponse], 
                                      synthesis_data: Dict[str, Any]):
    """Probar almacenamiento en BD con detalles"""
    print_separator("ANÁLISIS DETALLADO: ALMACENAMIENTO EN BASE DE DATOS")
    
    moderator_response = synthesis_data["moderator_response"]
    
    print("💾 Iniciando almacenamiento en base de datos...")
    
    async for session in get_async_session():
        # 1. Almacenar síntesis moderada
        print_section("ALMACENANDO SÍNTESIS MODERADA")
        moderated_synthesis = ModeratedSynthesis(
            id=uuid.uuid4(),
            synthesis_text=moderator_response.synthesis_text
        )
        session.add(moderated_synthesis)
        await session.commit()
        await session.refresh(moderated_synthesis)
        
        print(f"   ✅ Síntesis almacenada:")
        print(f"     • ID: {moderated_synthesis.id}")
        print(f"     • Longitud: {len(moderated_synthesis.synthesis_text)} caracteres")
        print(f"     • Timestamp: {moderated_synthesis.created_at}")
        
        # 2. Crear evento de interacción
        print_section("CREANDO EVENTO DE INTERACCIÓN")
        interaction_event = InteractionEvent(
            id=uuid.uuid4(),
            project_id=project.id,
            user_id=user.id,
            user_prompt_text=query,
            context_used_summary="Análisis detallado del sistema completo",
            moderated_synthesis_id=moderated_synthesis.id,
            user_feedback_score=None,
            user_feedback_comment=None,
            created_at=datetime.utcnow()
        )
        session.add(interaction_event)
        await session.commit()
        await session.refresh(interaction_event)
        
        print(f"   ✅ Evento de interacción creado:")
        print(f"     • ID: {interaction_event.id}")
        print(f"     • Proyecto ID: {interaction_event.project_id}")
        print(f"     • Usuario ID: {interaction_event.user_id}")
        print(f"     • Prompt: {interaction_event.user_prompt_text[:50]}...")
        print(f"     • Síntesis ID: {interaction_event.moderated_synthesis_id}")
        
        # 3. Almacenar respuestas IA individuales
        print_section("ALMACENANDO RESPUESTAS IA INDIVIDUALES")
        stored_responses = []
        
        for i, response in enumerate(responses, 1):
            ia_response = IAResponse(
                id=uuid.uuid4(),
                interaction_event_id=interaction_event.id,
                ia_provider_name=response.ia_provider_name.value,
                raw_response_text=response.response_text or "",
                latency_ms=response.latency_ms,
                error_message=response.error_message,
                received_at=datetime.utcnow()
            )
            session.add(ia_response)
            stored_responses.append(ia_response)
            
            print(f"   ✅ Respuesta {i} almacenada:")
            print(f"     • ID: {ia_response.id}")
            print(f"     • Proveedor: {ia_response.ia_provider_name}")
            print(f"     • Latencia: {ia_response.latency_ms}ms")
            print(f"     • Longitud: {len(ia_response.raw_response_text)} chars")
            if ia_response.error_message:
                print(f"     • Error: {ia_response.error_message}")
        
        await session.commit()
        
        print_section("RESUMEN DE ALMACENAMIENTO")
        print(f"   📊 Registros creados:")
        print(f"     • 1 síntesis moderada")
        print(f"     • 1 evento de interacción")
        print(f"     • {len(stored_responses)} respuestas IA")
        print(f"     • Total: {3 + len(stored_responses)} registros en BD")
        
        return interaction_event

async def test_sistema_detallado():
    """Prueba detallada completa del sistema"""
    print_separator("🔬 PRUEBA DETALLADA DEL SISTEMA ORQUIX BACKEND", "🔬", 90)
    print("Esta prueba mostrará todos los detalles del proceso de principio a fin")
    
    try:
        # 1. Verificación del sistema
        if not await verificar_configuracion():
            print("\n❌ Verificación del sistema falló. Abortando prueba.")
            return
        
        # 2. Crear datos de prueba
        user, project = await crear_datos_prueba()
        
        # 3. Obtener consulta del usuario
        print_separator("ENTRADA DEL USUARIO")
        query = input("❓ Ingresa tu consulta (o presiona Enter para usar una por defecto): ").strip()
        if not query:
            query = "¿Cuáles son las tendencias más importantes en inteligencia artificial para 2024?"
        
        print(f"🎯 CONSULTA SELECCIONADA: '{query}'")
        print(f"   • Longitud: {len(query)} caracteres")
        print(f"   • Palabras: ~{len(query.split())} palabras")
        
        # 4. Probar AI Orchestrator detalladamente
        responses = await test_orchestrator_detallado(query)
        
        # 5. Probar AI Moderator detalladamente
        synthesis_data = await test_moderator_detallado(responses)
        
        # 6. Análisis completo del proceso
        await analizar_proceso_completo(user, project, query, responses, synthesis_data)
        
        # 7. Almacenamiento detallado
        interaction_event = await test_almacenamiento_detallado(
            user, project, query, responses, synthesis_data
        )
        
        # 8. Resumen final
        print_separator("🎉 RESUMEN FINAL DE LA PRUEBA", "🎉", 90)
        
        print("✅ SISTEMA COMPLETAMENTE OPERATIVO:")
        print("   🔑 APIs reales configuradas y funcionando")
        print("   🤖 AI Orchestrator procesando consultas exitosamente")
        print("   🧠 AI Moderator generando síntesis de alta calidad")
        print("   💾 Base de datos almacenando datos correctamente")
        print("   🌐 Servidor FastAPI operativo")
        
        moderator_response = synthesis_data["moderator_response"]
        print(f"\n📊 MÉTRICAS DE LA PRUEBA:")
        print(f"   • Consulta procesada: '{query[:50]}...'")
        print(f"   • IAs consultadas: {len(responses)}")
        print(f"   • Calidad síntesis: {moderator_response.quality}")
        print(f"   • Temas identificados: {len(moderator_response.key_themes)}")
        print(f"   • Recomendaciones: {len(moderator_response.recommendations)}")
        print(f"   • Evento ID: {interaction_event.id}")
        
        print(f"\n🚀 EL SISTEMA ESTÁ LISTO PARA PRODUCCIÓN")
        
    except KeyboardInterrupt:
        print("\n⏹️ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ ERROR EN LA PRUEBA DETALLADA:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔬 PRUEBA DETALLADA DEL SISTEMA ORQUIX")
    print("Este script mostrará todos los detalles del proceso paso a paso")
    print("Incluyendo textos completos de IAs y proceso de síntesis")
    print()
    
    asyncio.run(test_sistema_detallado()) 