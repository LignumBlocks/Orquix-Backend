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

async def debug_context_flow():
    """Debug del flujo de contexto para ver qué se envía a las IAs"""
    
    print("🔍 DEBUG: Analizando flujo de contexto...")
    
    # Configurar base de datos
    database_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    engine = create_engine(database_url, echo=False)
    
    with Session(engine) as session:
        query_service = QueryService()
        context_manager = ContextManager(session)
        
        # Crear datos de prueba
        project_id = uuid4()
        user_id = uuid4()
        
        # Setup básico
        session.execute(sql_text("""
            INSERT INTO users (id, created_at, updated_at, email, name, google_id)
            VALUES (:user_id, NOW(), NOW(), :email, :name, :google_id)
        """), {
            "user_id": str(user_id),
            "email": f"test_{user_id}@example.com",
            "name": "Usuario Debug",
            "google_id": f"google_{user_id}"
        })
        
        session.execute(sql_text("""
            INSERT INTO projects (id, created_at, updated_at, name, description, user_id, 
                                moderator_personality, moderator_temperature, moderator_length_penalty)
            VALUES (:project_id, NOW(), NOW(), :name, :description, :user_id, 
                    :moderator_personality, :moderator_temperature, :moderator_length_penalty)
        """), {
            "project_id": str(project_id),
            "name": "Proyecto Debug",
            "description": "Debug del contexto",
            "user_id": str(user_id),
            "moderator_personality": "neutral",
            "moderator_temperature": 0.7,
            "moderator_length_penalty": 1.0
        })
        session.commit()
        
        # Crear documento con información clara
        documento = """
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
        
        Para ejecutar: uvicorn main:app --reload
        """
        
        print("📄 Documento a procesar:")
        print("-" * 50)
        print(documento)
        print("-" * 50)
        
        # Procesar documento
        chunks_text = context_manager.create_chunks(documento.strip())
        print(f"\n📊 Chunks generados: {len(chunks_text)}")
        
        for i, chunk in enumerate(chunks_text, 1):
            print(f"\n📄 CHUNK #{i}:")
            print(f"Longitud: {len(chunk)} caracteres")
            print("Contenido:")
            print("┌" + "─" * 48 + "┐")
            for line in chunk.split('\n'):
                print(f"│ {line:<46} │")
            print("└" + "─" * 48 + "┘")
            
            # Generar embedding y almacenar
            embedding = await context_manager.generate_embedding(chunk)
            chunk_data = ChunkCreate(
                project_id=project_id,
                user_id=user_id,
                content_text=chunk,
                content_embedding=embedding,
                source_type="tutorial",
                source_identifier="debug_doc"
            )
            stored_chunk = create_context_chunk_sync(session, chunk_data)
            print(f"✅ Chunk almacenado con ID: {stored_chunk.id}")
        
        # Ahora hacer la consulta
        print("\n🔍 Realizando consulta...")
        query_request = QueryRequest(
            user_question="¿Cómo instalo FastAPI?",
            project_id=project_id,
            user_id=user_id,
            query_type=QueryType.CONTEXT_AWARE,
            ai_providers=[AIProviderEnum.OPENAI],  # Solo OpenAI para simplificar
            context_config=ContextConfig(
                top_k=5,
                similarity_threshold=0.5,  # Umbral más bajo
                max_context_length=3000
            ),
            max_tokens=300,
            temperature=0.7
        )
        
        # Interceptar el proceso para ver el contexto
        print("\n🔍 Buscando contexto relevante...")
        
        # Buscar contexto manualmente para debug
        query_embedding = await context_manager.generate_embedding(query_request.user_question)
        
        from app.crud.context import find_similar_chunks_sync
        
        chunks = find_similar_chunks_sync(
            db=session,
            query_embedding=query_embedding,
            project_id=project_id,
            user_id=user_id,
            top_k=5,
            similarity_threshold=None  # Sin umbral para ver todos
        )
        
        print(f"📊 Chunks encontrados: {len(chunks)}")
        
        for i, chunk in enumerate(chunks, 1):
            # Calcular similitud
            import numpy as np
            vec1 = np.array(query_embedding)
            vec2 = np.array(chunk.content_embedding)
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            
            print(f"\n📄 CHUNK ENCONTRADO #{i}:")
            print(f"Similitud: {similarity:.4f} ({similarity*100:.1f}%)")
            print(f"Contenido:")
            print("┌" + "─" * 48 + "┐")
            for line in chunk.content_text.split('\n'):
                print(f"│ {line:<46} │")
            print("└" + "─" * 48 + "┘")
        
        # Ahora ejecutar la consulta completa
        print("\n🚀 Ejecutando consulta completa...")
        response = await query_service.process_query(query_request, session)
        
        print(f"\n📋 Resultado:")
        print(f"Context info: {response.context_info}")
        if response.context_info:
            print(f"📄 CONTEXTO ENVIADO A LA IA:")
            print("=" * 60)
            print(response.context_info.context_text)
            print("=" * 60)
        
        for ai_response in response.ai_responses:
            print(f"\n🤖 {ai_response.ia_provider_name.value}:")
            print(f"Estado: {ai_response.status.value}")
            print(f"Respuesta: {ai_response.response_text}")
        
        await query_service.close()

if __name__ == "__main__":
    asyncio.run(debug_context_flow()) 