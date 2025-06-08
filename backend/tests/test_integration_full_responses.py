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

async def test_complete_integration_with_full_responses():
    """
    Test de integración completo que muestra las respuestas COMPLETAS de las IAs
    """
    print("\n🚀 Iniciando prueba de integración con respuestas completas...")
    
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
                INSERT INTO users (id, created_at, updated_at, email, name, google_id, avatar_url)
                VALUES (:user_id, NOW(), NOW(), :email, :name, :google_id, :avatar_url)
            """), {
                "user_id": str(user_id),
                "email": f"test_{user_id}@example.com",
                "name": "Usuario de Prueba",
                "google_id": f"google_{user_id}",
                "avatar_url": "https://example.com/avatar.jpg"
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
            return False
        
        # 2. Procesar documentos de contexto
        print("\n📚 Paso 2: Procesando documentos de contexto...")
        
        documentos = [
            {
                "texto": """
                FastAPI es un framework web moderno para construir APIs con Python 3.6+.
                Sus principales características son:
                - Muy alto rendimiento, comparable a NodeJS y Go
                - Validación automática de datos usando Pydantic
                - Documentación automática con OpenAPI (Swagger)
                - Soporte nativo para async/await
                - Type hints de Python para mejor desarrollo
                - Fácil de aprender y usar
                """,
                "tipo": "documentacion",
                "id": "doc_fastapi"
            },
            {
                "texto": """
                Para instalar FastAPI necesitas:
                1. Python 3.6 o superior instalado en tu sistema
                2. Instalar fastapi con pip: pip install fastapi
                3. Instalar uvicorn para el servidor ASGI: pip install uvicorn[standard]
                
                Ejemplo básico de aplicación:
                from fastapi import FastAPI
                
                app = FastAPI()
                
                @app.get("/")
                def read_root():
                    return {"Hello": "World"}
                
                @app.get("/items/{item_id}")
                def read_item(item_id: int, q: str = None):
                    return {"item_id": item_id, "q": q}
                
                Para ejecutar: uvicorn main:app --reload
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
                return False
        
        print(f"   📊 Total chunks almacenados: {len(stored_chunks)}")
        
        # 3. Simular consulta de usuario
        print("\n🔍 Paso 3: Procesando consulta de usuario...")
        
        query_request = QueryRequest(
            user_question="¿Cómo instalo y configuro FastAPI paso a paso?",
            project_id=project_id,
            user_id=user_id,
            query_type=QueryType.CONTEXT_AWARE,
            ai_providers=[AIProviderEnum.OPENAI, AIProviderEnum.ANTHROPIC],
            context_config=ContextConfig(
                top_k=3,
                similarity_threshold=0.7,
                max_context_length=2000
            ),
            max_tokens=800,  # Más tokens para respuestas más completas
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
                print(f"   📄 Contexto usado:")
                print("   " + "="*60)
                # Mostrar el contexto que se envió a las IAs
                context_lines = response.context_info.context_text.split('\n')
                for line in context_lines[:10]:  # Primeras 10 líneas del contexto
                    if line.strip():
                        print(f"   {line}")
                print("   " + "="*60)
            
            print("\n🤖 RESPUESTAS COMPLETAS DE LAS IAs:")
            print("="*80)
            
            for i, ai_response in enumerate(response.ai_responses, 1):
                print(f"\n🤖 RESPUESTA #{i}: {ai_response.ia_provider_name.value.upper()}")
                print("-" * 60)
                print(f"📊 Estado: {ai_response.status.value}")
                print(f"⏱️  Latencia: {ai_response.latency_ms}ms")
                
                if ai_response.response_text:
                    print(f"📝 RESPUESTA COMPLETA:")
                    print("┌" + "─" * 58 + "┐")
                    # Dividir la respuesta en líneas y formatear
                    response_lines = ai_response.response_text.split('\n')
                    for line in response_lines:
                        # Dividir líneas largas
                        if len(line) > 56:
                            words = line.split(' ')
                            current_line = ""
                            for word in words:
                                if len(current_line + word) > 56:
                                    print(f"│ {current_line:<56} │")
                                    current_line = word + " "
                                else:
                                    current_line += word + " "
                            if current_line.strip():
                                print(f"│ {current_line.strip():<56} │")
                        else:
                            print(f"│ {line:<56} │")
                    print("└" + "─" * 58 + "┘")
                
                if ai_response.usage_info:
                    print(f"📊 Uso de tokens: {ai_response.usage_info}")
                
                if ai_response.error_message:
                    print(f"❌ Error: {ai_response.error_message}")
                
                print("-" * 60)
            
            print("\n✅ Test de integración con respuestas completas finalizado!")
            return True
            
        except Exception as e:
            print(f"\n❌ Error en la consulta: {e}")
            return False
        
        finally:
            # Limpieza
            await query_service.close()

if __name__ == "__main__":
    result = asyncio.run(test_complete_integration_with_full_responses())
    if result:
        print("\n🎯 RESULTADO: Test exitoso con respuestas completas")
    else:
        print("\n💥 RESULTADO: Test falló") 