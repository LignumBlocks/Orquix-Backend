import pytest
import asyncio
from uuid import uuid4
from sqlmodel import Session, create_engine
from sqlalchemy import text as sql_text

from app.services.query_service import QueryService
from app.services.context_manager import ContextManager
from app.core.config import settings
from app.schemas.query import QueryRequest, QueryType, ContextConfig
from app.schemas.ai_response import AIProviderEnum
from app.crud.context import create_context_chunk_sync
from app.schemas.context import ChunkCreate

async def test_complete_integration_flow():
    """
    Test de integración completo que simula:
    1. Creación de usuario y proyecto
    2. Ingesta y procesamiento de documentos de contexto
    3. Consulta del usuario con búsqueda de contexto
    4. Generación de respuestas por múltiples IAs
    """
    print("\n🚀 Iniciando prueba de integración completa del flujo...")
    
    # Configurar base de datos
    database_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    engine = create_engine(database_url, echo=False)
    
    with Session(engine) as session:
        # Inicializar servicios
        query_service = QueryService()
        context_manager = ContextManager(session)
        
        # 1. Crear datos de prueba
        project_id = uuid4()
        user_id = uuid4()
        
        print("\n👤 Paso 1: Creando usuario y proyecto de prueba...")
        try:
            # Crear usuario de prueba
            session.execute(sql_text("""
                INSERT INTO users (id, created_at, updated_at, email, name, google_id)
                VALUES (:user_id, NOW(), NOW(), :email, :name, :google_id)
            """), {
                "user_id": str(user_id),
                "email": f"test_{user_id}@example.com",
                "name": "Usuario de Prueba",
                "google_id": f"google_{user_id}"
            })
            
            # Crear proyecto de prueba
            session.execute(sql_text("""
                INSERT INTO projects (id, created_at, updated_at, name, description, user_id, 
                                    moderator_personality, moderator_temperature, moderator_length_penalty)
                VALUES (:project_id, NOW(), NOW(), :name, :description, :user_id, 
                        :moderator_personality, :moderator_temperature, :moderator_length_penalty)
            """), {
                "project_id": str(project_id),
                "name": "Proyecto Test Integral",
                "description": "Proyecto para prueba de integración completa",
                "user_id": str(user_id),
                "moderator_personality": "neutral",
                "moderator_temperature": 0.7,
                "moderator_length_penalty": 1.0
            })
            
            session.commit()
            print("   ✅ Usuario y proyecto creados exitosamente")
            
        except Exception as e:
            print(f"   ❌ Error creando datos iniciales: {e}")
            pytest.fail("Error en setup inicial")
        
        # 2. Procesar documentos de contexto
        print("\n📚 Paso 2: Procesando documentos de contexto...")
        
        documentos = [
            {
                "texto": """
                FastAPI es un framework web moderno para construir APIs con Python 3.6+.
                Sus principales características son:
                - Muy alto rendimiento
                - Validación automática de datos
                - Documentación automática con OpenAPI
                - Soporte nativo para async/await
                """,
                "tipo": "documentacion",
                "id": "doc_fastapi"
            },
            {
                "texto": """
                Para instalar FastAPI necesitas:
                1. Python 3.6 o superior
                2. Instalar fastapi con pip: pip install fastapi
                3. Instalar uvicorn para el servidor: pip install uvicorn
                
                Ejemplo básico:
                from fastapi import FastAPI
                app = FastAPI()
                
                @app.get("/")
                def read_root():
                    return {"Hello": "World"}
                """,
                "tipo": "tutorial",
                "id": "tutorial_fastapi"
            }
        ]
        
        stored_chunks = []
        for doc in documentos:
            try:
                # Dividir en chunks
                chunks_text = context_manager.create_chunks(doc["texto"].strip())
                
                for chunk_text in chunks_text:
                    # Generar embedding
                    embedding = await context_manager.generate_embedding(chunk_text)
                    
                    # Crear y almacenar chunk
                    chunk_data = ChunkCreate(
                        project_id=project_id,
                        user_id=user_id,
                        content_text=chunk_text,
                        content_embedding=embedding,
                        source_type=doc["tipo"],
                        source_identifier=doc["id"]
                    )
                    chunk = create_context_chunk_sync(session, chunk_data)
                    stored_chunks.append(chunk)
                
                print(f"   ✅ Documento {doc['id']}: {len(chunks_text)} chunks procesados")
                
            except Exception as e:
                print(f"   ❌ Error procesando documento {doc['id']}: {e}")
                pytest.fail("Error procesando documentos")
        
        print(f"   📊 Total chunks almacenados: {len(stored_chunks)}")
        
        # 3. Simular consulta de usuario
        print("\n🔍 Paso 3: Procesando consulta de usuario...")
        
        query_request = QueryRequest(
            user_question="¿Cómo instalo y configuro FastAPI?",
            project_id=project_id,
            user_id=user_id,
            query_type=QueryType.CONTEXT_AWARE,
            ai_providers=[AIProviderEnum.OPENAI, AIProviderEnum.ANTHROPIC],
            context_config=ContextConfig(
                top_k=3,
                similarity_threshold=0.7,
                max_context_length=2000
            ),
            max_tokens=500,
            temperature=0.7
        )
        
        try:
            response = await query_service.process_query(query_request, session)
            
            print("\n📋 Resultados de la consulta:")
            print(f"   ⏱️  Tiempo total: {response.processing_time_ms}ms")
            print(f"   🤖 Proveedores usados: {[p.value for p in response.providers_used]}")
            
            if response.context_info:
                print(f"   📚 Chunks de contexto: {response.context_info.total_chunks}")
                print(f"   📊 Similitud promedio: {response.context_info.avg_similarity:.2%}")
            
            print("\n🤖 Respuestas de IAs:")
            for ai_response in response.ai_responses:
                print(f"\n   {ai_response.ia_provider_name.value}:")
                print(f"   - Estado: {ai_response.status.value}")
                print(f"   - Latencia: {ai_response.latency_ms}ms")
                if ai_response.response_text:
                    print(f"   - Respuesta: {ai_response.response_text[:100]}...")
                if ai_response.error_message:
                    print(f"   - Error: {ai_response.error_message}")
            
            # Verificaciones básicas
            assert response.original_question == query_request.user_question
            assert len(response.ai_responses) > 0
            if response.context_info:
                assert response.context_info.total_chunks > 0
            
            print("\n✅ Test de integración completado exitosamente!")
            
        except Exception as e:
            print(f"\n❌ Error en la consulta: {e}")
            pytest.fail("Error procesando la consulta")
        
        finally:
            # Limpieza
            await query_service.close()

if __name__ == "__main__":
    asyncio.run(test_complete_integration_flow()) 