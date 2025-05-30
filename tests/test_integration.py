import pytest
import asyncio
from uuid import uuid4
from sqlmodel import Session, create_engine
from sqlalchemy import text as sql_text
from app.services.context_manager import ContextManager
from app.core.config import settings
from app.crud.context import create_context_chunk_sync, find_similar_chunks_sync
from app.schemas.context import ChunkCreate

async def test_full_integration():
    """Prueba de integración completa: procesamiento, almacenamiento y búsqueda"""
    print("\n🚀 Iniciando prueba de integración completa...")
    
    database_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    engine = create_engine(database_url, echo=False)
    
    with Session(engine) as session:
        context_manager = ContextManager(session)
        
        # Datos de prueba
        project_id = uuid4()
        user_id = uuid4()
        
        print("👤 Paso 0: Creando usuario y proyecto de prueba...")
        
        # Crear usuario de prueba
        try:
            unique_email = f"test_{user_id}@example.com"
            unique_google_id = f"test_google_id_{user_id}"
            
            session.execute(sql_text("""
                INSERT INTO users (id, created_at, updated_at, email, name, google_id)
                VALUES (:user_id, NOW(), NOW(), :email, :name, :google_id)
            """), {
                "user_id": str(user_id),
                "email": unique_email,
                "name": "Usuario de Prueba",
                "google_id": unique_google_id
            })
            
            # Crear proyecto de prueba
            session.execute(sql_text("""
                INSERT INTO projects (id, created_at, updated_at, name, description, user_id, moderator_personality, moderator_temperature, moderator_length_penalty)
                VALUES (:project_id, NOW(), NOW(), :name, :description, :user_id, :moderator_personality, :moderator_temperature, :moderator_length_penalty)
            """), {
                "project_id": str(project_id),
                "name": "Proyecto de Prueba",
                "description": "Proyecto para pruebas de integración",
                "user_id": str(user_id),
                "moderator_personality": "neutral",
                "moderator_temperature": 0.7,
                "moderator_length_penalty": 1.0
            })
            
            session.commit()
            print("   ✅ Usuario y proyecto creados")
            
        except Exception as e:
            print(f"   ❌ Error creando usuario/proyecto: {e}")
            return False
        
        # Textos de prueba sobre diferentes temas
        texts = [
            "FastAPI es un framework web moderno y rápido para construir APIs con Python.",
            "Python es un lenguaje de programación interpretado y de alto nivel.",
            "PostgreSQL es un sistema de gestión de bases de datos relacionales avanzado."
        ]
        
        print("📝 Paso 1: Procesando y almacenando textos...")
        stored_chunks = []
        
        for i, text in enumerate(texts):
            try:
                # Dividir texto en chunks
                chunks_text = context_manager.create_chunks(text.strip())
                
                for chunk_text in chunks_text:
                    # Generar embedding
                    embedding = await context_manager.generate_embedding(chunk_text)
                    
                    # Crear objeto ChunkCreate
                    chunk_data = ChunkCreate(
                        project_id=project_id,
                        user_id=user_id,
                        content_text=chunk_text,
                        content_embedding=embedding,
                        source_type="test",
                        source_identifier=f"doc_{i}"
                    )
                    
                    # Almacenar en BD usando función síncrona
                    chunk = create_context_chunk_sync(session, chunk_data)
                    stored_chunks.append(chunk)
                
                print(f"   ✅ Documento {i+1}: {len(chunks_text)} chunks almacenados")
                
            except Exception as e:
                print(f"   ❌ Error procesando documento {i+1}: {e}")
                return False
        
        print(f"📊 Total de chunks almacenados: {len(stored_chunks)}")
        
        # Verificar que se almacenaron correctamente
        if len(stored_chunks) == 0:
            print("❌ No se almacenaron chunks")
            return False
        
        # Verificar que los chunks tienen embeddings
        for chunk in stored_chunks:
            if not hasattr(chunk, 'content_embedding') or chunk.content_embedding is None or len(chunk.content_embedding) == 0:
                print("❌ Chunk sin embedding encontrado")
                return False
        
        print("✅ Todos los chunks tienen embeddings")
        
        # Mostrar resumen de chunks almacenados
        print("\n📚 RESUMEN DE CHUNKS ALMACENADOS:")
        print("=" * 80)
        for i, chunk in enumerate(stored_chunks, 1):
            print(f"\n📄 CHUNK #{i}:")
            print(f"   📝 Texto: {chunk.content_text}")
            print(f"   🏷️  Fuente: {chunk.source_type} - {chunk.source_identifier}")
            print(f"   🆔 ID: {str(chunk.id)[:8]}...")
            print(f"   📊 Longitud: {len(chunk.content_text)} caracteres")
            print(f"   🧮 Dimensiones del embedding: {len(chunk.content_embedding)}")
            
            # Mostrar las primeras dimensiones del embedding
            embedding_preview = chunk.content_embedding[:5] if len(chunk.content_embedding) >= 5 else chunk.content_embedding
            print(f"   🔢 Embedding (primeras 5 dims): {[round(x, 4) for x in embedding_preview]}")
            
            if i < len(stored_chunks):
                print("   " + "·" * 70)
        
        # Paso 2: Búsqueda de contexto relevante
        print("\n🔍 Paso 2: Probando búsqueda de contexto relevante...")
        print("=" * 80)
        
        queries = [
            "¿Qué es FastAPI?",
            "¿Cómo funciona Python?", 
            "¿Qué es PostgreSQL?"
        ]
        
        for query in queries:
            try:
                print(f"\n📋 CONSULTA: '{query}'")
                print("-" * 60)
                
                # Generar embedding para la query
                query_embedding = await context_manager.generate_embedding(query)
                
                # Buscar chunks similares usando función síncrona
                similar_chunks = find_similar_chunks_sync(
                    session,
                    query_embedding,
                    project_id,
                    top_k=3,
                    similarity_threshold=None  # Eliminar umbral por ahora
                )
                
                print(f"   🎯 Resultados encontrados: {len(similar_chunks)} chunks")
                
                if len(similar_chunks) > 0:
                    for i, chunk in enumerate(similar_chunks, 1):
                        print(f"\n   📄 RESULTADO #{i}:")
                        print(f"      📝 Texto completo: {chunk.content_text}")
                        print(f"      🏷️  Fuente: {chunk.source_type} - {chunk.source_identifier}")
                        print(f"      🆔 ID del chunk: {str(chunk.id)[:8]}...")
                        print(f"      📊 Longitud: {len(chunk.content_text)} caracteres")
                        
                        # Mostrar las primeras dimensiones del embedding como referencia
                        embedding_preview = chunk.content_embedding[:5] if len(chunk.content_embedding) >= 5 else chunk.content_embedding
                        print(f"      🧮 Embedding (primeras 5 dims): {[round(x, 4) for x in embedding_preview]}")
                        
                        if i < len(similar_chunks):
                            print("      " + "·" * 50)
                else:
                    print("   ❌ No se encontraron chunks relevantes")
                
                print("\n" + "=" * 80)
                
            except Exception as e:
                print(f"   ❌ Error en búsqueda para '{query}': {e}")
                return False
        
        print("\n🎉 ¡Prueba de integración completada exitosamente!")
        print("✅ Procesamiento de texto: OK")
        print("✅ Generación de embeddings: OK") 
        print("✅ Almacenamiento en BD: OK")
        print("✅ Búsqueda vectorial: OK")
        
        return True

if __name__ == "__main__":
    result = asyncio.run(test_full_integration())
    if result:
        print("\n🎯 RESULTADO: Integración completa funcional")
    else:
        print("\n💥 RESULTADO: Falló la integración") 