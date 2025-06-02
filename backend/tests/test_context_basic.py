import pytest
from uuid import uuid4
from sqlmodel import Session, create_engine
from app.services.context_manager import ContextManager
from app.core.config import settings

def test_context_manager_creation():
    """Prueba la creación del ContextManager"""
    database_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    engine = create_engine(database_url, echo=False)
    
    with Session(engine) as session:
        context_manager = ContextManager(session)
        assert context_manager is not None
        assert context_manager.db == session
        assert context_manager.embedding_model == "text-embedding-3-small"
        print("✅ ContextManager creado exitosamente")

def test_create_chunks():
    """Prueba la división de texto en chunks"""
    database_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    engine = create_engine(database_url, echo=False)
    
    with Session(engine) as session:
        context_manager = ContextManager(session)
        
        text = """
        Este es un texto de prueba para dividir en chunks.
        Contiene múltiples párrafos para probar la funcionalidad.
        
        Este es el segundo párrafo del texto de prueba.
        Debería ser dividido correctamente en chunks semánticamente coherentes.
        """
        
        chunks = context_manager.create_chunks(text)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk.strip()) > 0 for chunk in chunks)
        print(f"✅ Texto dividido en {len(chunks)} chunks")

if __name__ == "__main__":
    test_context_manager_creation()
    test_create_chunks()
    print("✅ Todas las pruebas básicas del ContextManager pasaron") 