import pytest
import asyncio
from uuid import uuid4
from sqlmodel import Session, create_engine
from sqlalchemy import text as sql_text

from app.services.query_service import QueryService
from app.schemas.query import QueryRequest, QueryType, ContextConfig
from app.schemas.ai_response import AIProviderEnum, AIResponseStatus
from app.core.config import settings
from app.services.context_manager import ContextManager
from app.schemas.context import ChunkCreate

async def test_full_query_pipeline():
    """
    Test completo que demuestra la Tarea 2.2:
    1. Preparar datos de contexto
    2. Hacer consulta con búsqueda de contexto
    3. Construcción de prompts específicos
    4. Ejecución paralela a múltiples IAs
    5. Agregación de respuestas
    """
    print("\n🚀 INICIANDO TEST COMPLETO DE QUERY SERVICE")
    print("=" * 80)
    
    # Configurar BD
    database_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    engine = create_engine(database_url, echo=False)
    
    with Session(engine) as session:
        # Paso 0: Crear datos de prueba
        project_id = uuid4()
        user_id = uuid4()
        
        print("📋 PASO 0: Preparando datos de prueba...")
        await setup_test_data(session, project_id, user_id)
        print("   ✅ Datos de prueba creados")
        
        # Paso 1: Inicializar el servicio
        print("\n🔧 PASO 1: Inicializando Query Service...")
        query_service = QueryService()
        print("   ✅ Query Service inicializado")
        
        # Paso 2: Crear consulta con búsqueda de contexto
        print("\n❓ PASO 2: Creando consulta de prueba...")
        
        query_request = QueryRequest(
            user_question="¿Qué framework web moderno puedo usar para crear APIs con Python?",
            project_id=project_id,
            user_id=user_id,
            query_type=QueryType.CONTEXT_AWARE,
            context_config=ContextConfig(
                top_k=3,
                similarity_threshold=0.6,
                max_context_length=2000
            ),
            ai_providers=[AIProviderEnum.OPENAI],  # Usar solo OpenAI por ahora
            temperature=0.7,
            max_tokens=200
        )
        
        print(f"   📝 Pregunta: '{query_request.user_question}'")
        print(f"   🎯 Tipo de consulta: {query_request.query_type}")
        print(f"   🤖 Proveedores: {query_request.ai_providers}")
        
        # Paso 3: Procesar consulta completa
        print("\n⚡ PASO 3: Procesando consulta completa...")
        print("   → Buscando contexto relevante...")
        print("   → Construyendo prompts específicos...")
        print("   → Ejecutando consultas en paralelo...")
        
        response = await query_service.process_query(query_request, session)
        
        print(f"   ✅ Consulta completada en {response.processing_time_ms}ms")
        
        # Paso 4: Analizar resultados
        print("\n📊 PASO 4: Analizando resultados...")
        print("=" * 80)
        
        # Información del contexto
        if response.context_info:
            print("🔍 CONTEXTO ENCONTRADO:")
            print(f"   📄 Total de chunks: {response.context_info.total_chunks}")
            print(f"   🎯 Similitud promedio: {response.context_info.avg_similarity:.1%}")
            print(f"   📚 Fuentes utilizadas: {response.context_info.sources_used}")
            print(f"   📊 Total caracteres: {response.context_info.total_characters}")
            
            print("\n📝 CONTEXTO FORMATEADO:")
            print("-" * 60)
            context_preview = response.context_info.context_text[:500]
            print(f"{context_preview}..." if len(response.context_info.context_text) > 500 else response.context_info.context_text)
            print("-" * 60)
        else:
            print("⚠️  No se encontró contexto relevante")
        
        # Respuestas de las IAs
        print(f"\n🤖 RESPUESTAS DE IAs ({len(response.ai_responses)} total):")
        print("=" * 80)
        
        for i, ai_response in enumerate(response.ai_responses, 1):
            print(f"\n📋 RESPUESTA #{i} - {ai_response.ia_provider_name.upper()}")
            print(f"   📊 Estado: {ai_response.status}")
            print(f"   ⏱️  Latencia: {ai_response.latency_ms}ms")
            
            if ai_response.status == AIResponseStatus.SUCCESS:
                print(f"   💬 Respuesta:")
                response_text = ai_response.response_text or ""
                if len(response_text) > 300:
                    print(f"      {response_text[:300]}...")
                else:
                    print(f"      {response_text}")
                
                if ai_response.usage_info:
                    print(f"   📈 Uso de tokens: {ai_response.usage_info}")
            else:
                print(f"   ❌ Error: {ai_response.error_message}")
            
            print("   " + "-" * 70)
        
        # Metadatos de la consulta
        print(f"\n📈 METADATOS DE LA CONSULTA:")
        print(f"   🕒 Tiempo total: {response.processing_time_ms}ms")
        print(f"   🤖 Proveedores usados: {response.providers_used}")
        print(f"   ✅ Respuestas exitosas: {response.metadata.get('successful_responses', 0)}")
        
        # Verificaciones
        print(f"\n✅ VERIFICACIONES:")
        
        # Verificar que se encontró contexto
        context_found = response.context_info is not None
        print(f"   📄 Contexto encontrado: {context_found}")
        
        # Verificar que hay respuestas
        has_responses = len(response.ai_responses) > 0
        print(f"   🤖 Respuestas recibidas: {has_responses}")
        
        # Verificar que al menos una respuesta fue exitosa
        successful_responses = [r for r in response.ai_responses if r.status == AIResponseStatus.SUCCESS]
        has_success = len(successful_responses) > 0
        print(f"   ✅ Al menos una respuesta exitosa: {has_success}")
        
        # Verificar que el contexto incluye información sobre FastAPI
        context_has_fastapi = False
        if response.context_info:
            context_has_fastapi = "fastapi" in response.context_info.context_text.lower()
        print(f"   🎯 Contexto incluye FastAPI: {context_has_fastapi}")
        
        # Verificar que la respuesta menciona FastAPI
        response_mentions_fastapi = False
        if successful_responses:
            for resp in successful_responses:
                if resp.response_text and "fastapi" in resp.response_text.lower():
                    response_mentions_fastapi = True
                    break
        print(f"   💬 Respuesta menciona FastAPI: {response_mentions_fastapi}")
        
        await query_service.close()
        
        # Resultado final
        all_checks = [
            context_found,
            has_responses, 
            has_success,
            context_has_fastapi,
            response_mentions_fastapi
        ]
        
        success_rate = sum(all_checks) / len(all_checks)
        
        print(f"\n🎯 RESULTADO FINAL:")
        print(f"   ✅ Verificaciones exitosas: {sum(all_checks)}/{len(all_checks)} ({success_rate:.1%})")
        
        if success_rate >= 0.8:
            print("   🎉 ¡TEST EXITOSO! El pipeline completo funciona correctamente")
            return True
        else:
            print("   ⚠️  Test parcialmente exitoso, revisar verificaciones fallidas")
            return False

async def setup_test_data(session: Session, project_id, user_id):
    """Prepara datos de prueba en la base de datos"""
    
    # Crear usuario de prueba
    unique_email = f"test_{user_id}@example.com"
    unique_google_id = f"test_google_id_{user_id}"
    
    session.execute(sql_text("""
        INSERT INTO users (id, created_at, updated_at, email, name, google_id)
        VALUES (:user_id, NOW(), NOW(), :email, :name, :google_id)
    """), {
        "user_id": str(user_id),
        "email": unique_email,
        "name": "Usuario de Prueba Query",
        "google_id": unique_google_id
    })
    
    # Crear proyecto de prueba
    session.execute(sql_text("""
        INSERT INTO projects (id, created_at, updated_at, name, description, user_id, moderator_personality, moderator_temperature, moderator_length_penalty)
        VALUES (:project_id, NOW(), NOW(), :name, :description, :user_id, :moderator_personality, :moderator_temperature, :moderator_length_penalty)
    """), {
        "project_id": str(project_id),
        "name": "Proyecto Query Test",
        "description": "Proyecto para pruebas de queries completas",
        "user_id": str(user_id),
        "moderator_personality": "neutral",
        "moderator_temperature": 0.7,
        "moderator_length_penalty": 1.0
    })
    
    session.commit()
    
    # Crear contexto de prueba con ContextManager
    context_manager = ContextManager(session)
    
    # Textos de prueba relacionados con desarrollo web y Python
    test_texts = [
        "FastAPI es un framework web moderno y rápido para construir APIs con Python 3.6+ basado en estándares como OpenAPI y JSON Schema.",
        "Flask es un micro framework web escrito en Python que es fácil de aprender y usar para crear aplicaciones web.",
        "Django es un framework web de alto nivel escrito en Python que fomenta el desarrollo rápido y el diseño limpio.",
        "Python es un lenguaje de programación interpretado de alto nivel con sintaxis elegante y filosofía de diseño que enfatiza la legibilidad del código."
    ]
    
    for i, text in enumerate(test_texts):
        # Dividir en chunks
        chunks_text = context_manager.create_chunks(text.strip())
        
        for chunk_text in chunks_text:
            # Generar embedding
            embedding = await context_manager.generate_embedding(chunk_text)
            
            # Crear chunk
            chunk_data = ChunkCreate(
                project_id=project_id,
                user_id=user_id,
                content_text=chunk_text,
                content_embedding=embedding,
                source_type="documentation",
                source_identifier=f"web_framework_doc_{i}"
            )
            
            # Almacenar usando función síncrona
            from app.crud.context import create_context_chunk_sync
            create_context_chunk_sync(session, chunk_data)

if __name__ == "__main__":
    result = asyncio.run(test_full_query_pipeline())
    if result:
        print("\n🎯 RESULTADO GENERAL: Pipeline completo funcional! 🎉")
    else:
        print("\n💥 RESULTADO GENERAL: Revisar componentes del pipeline") 