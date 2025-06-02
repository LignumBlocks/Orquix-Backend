import pytest
import asyncio
from uuid import uuid4
from sqlmodel import Session, create_engine
from app.services.context_manager import ContextManager
from app.core.config import settings

async def test_generate_embedding():
    """Prueba la generación de embeddings con OpenAI"""
    database_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    engine = create_engine(database_url, echo=False)
    
    with Session(engine) as session:
        context_manager = ContextManager(session)
        
        text = "Este es un texto de prueba para generar embeddings."
        
        try:
            embedding = await context_manager.generate_embedding(text)
            
            assert embedding is not None
            assert isinstance(embedding, list)
            assert len(embedding) == 1536  # Dimensión de text-embedding-3-small
            assert all(isinstance(x, float) for x in embedding)
            
            print(f"✅ Embedding generado exitosamente con {len(embedding)} dimensiones")
            return True
            
        except Exception as e:
            print(f"❌ Error al generar embedding: {e}")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_generate_embedding())
    if result:
        print("✅ Prueba de embeddings completada exitosamente")
    else:
        print("❌ Prueba de embeddings falló") 