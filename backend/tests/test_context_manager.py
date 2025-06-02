import pytest
from uuid import uuid4
from sqlmodel import Session, create_engine
from app.services.context_manager import ContextManager, EmbeddingError
from app.core.config import settings
from app.schemas.context import ChunkResponse, ChunkWithSimilarity, ContextBlock

# Datos de prueba
SAMPLE_TEXTS = [
    """
    FastAPI es un framework moderno y rápido para construir APIs con Python.
    Se basa en Pydantic para la validación de datos y tipado.
    Ofrece documentación automática con Swagger UI y ReDoc.
    """,
    """
    La autenticación en FastAPI se puede implementar de varias formas.
    OAuth2 con JWT es una opción popular y segura.
    También se puede usar autenticación básica o por API key.
    """,
    """
    Los modelos en FastAPI usan Pydantic para definir su estructura.
    Esto permite validación automática y serialización de datos.
    La integración con ORMs como SQLAlchemy es sencilla.
    """
]

# Configuración de la base de datos de prueba
@pytest.fixture(scope="session")
def engine():
    # Usamos la misma base de datos pero con un esquema diferente para pruebas
    database_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    return create_engine(
        database_url,
        echo=False
    )

@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture
def context_manager(session):
    """Fixture que proporciona una instancia de ContextManager con una sesión de BD."""
    return ContextManager(session)

@pytest.fixture
async def sample_chunks(context_manager):
    """Fixture que carga los textos de ejemplo en la BD y retorna los chunks."""
    project_id = uuid4()
    user_id = uuid4()
    stored_chunks = []
    
    for i, text in enumerate(SAMPLE_TEXTS):
        chunks = await context_manager.process_and_store_text(
            text=text,
            project_id=project_id,
            user_id=user_id,
            source_type="test",
            source_identifier=f"test_{i}"
        )
        stored_chunks.extend(chunks)
    
    return {
        "chunks": stored_chunks,
        "project_id": project_id,
        "user_id": user_id
    }

@pytest.mark.asyncio
async def test_process_and_store_text(context_manager):
    """Prueba el procesamiento y almacenamiento de texto."""
    project_id = uuid4()
    user_id = uuid4()
    
    # Procesar un texto de ejemplo
    chunks = await context_manager.process_and_store_text(
        text=SAMPLE_TEXTS[0],
        project_id=project_id,
        user_id=user_id,
        source_type="test",
        source_identifier="test_0"
    )
    
    # Verificaciones
    assert len(chunks) > 0, "Debería generar al menos un chunk"
    for chunk in chunks:
        assert isinstance(chunk, ChunkResponse), "Cada chunk debe ser un ChunkResponse"
        assert chunk.content_text.strip(), "El texto del chunk no debe estar vacío"
        assert chunk.embedding is not None, "Debe tener un embedding"
        assert len(chunk.embedding) > 0, "El embedding debe tener dimensiones"

@pytest.mark.asyncio
async def test_find_relevant_context(context_manager, sample_chunks):
    """Prueba la búsqueda de contexto relevante."""
    query = "¿Cómo funciona la autenticación en FastAPI?"
    
    relevant_chunks = await context_manager.find_relevant_context(
        query=query,
        project_id=sample_chunks["project_id"],
        top_k=3,
        similarity_threshold=0.3
    )
    
    # Verificaciones
    assert len(relevant_chunks) > 0, "Debería encontrar chunks relevantes"
    assert len(relevant_chunks) <= 3, "No debe exceder top_k"
    
    for chunk in relevant_chunks:
        assert isinstance(chunk, ChunkWithSimilarity), "Debe retornar ChunkWithSimilarity"
        assert 0 <= chunk.similarity_score <= 1, "Similitud debe estar entre 0 y 1"
        
    # El chunk más relevante debe contener información sobre autenticación
    assert "autenticación" in relevant_chunks[0].chunk.content_text.lower()

@pytest.mark.asyncio
async def test_generate_context_block(context_manager, sample_chunks):
    """Prueba la generación de bloques de contexto."""
    query = "¿Cómo funciona la autenticación en FastAPI?"
    
    context_block = await context_manager.generate_context_block(
        query=query,
        project_id=sample_chunks["project_id"],
        top_k=3,
        similarity_threshold=0.3
    )
    
    # Verificaciones
    assert isinstance(context_block, ContextBlock), "Debe retornar un ContextBlock"
    assert context_block.context_text, "El texto de contexto no debe estar vacío"
    assert context_block.total_tokens > 0, "Debe tener tokens"
    assert context_block.chunks_used > 0, "Debe usar al menos un chunk"
    assert isinstance(context_block.was_truncated, bool), "was_truncated debe ser booleano"

@pytest.mark.asyncio
async def test_empty_query_handling(context_manager, sample_chunks):
    """Prueba el manejo de consultas vacías."""
    with pytest.raises(ValueError):
        await context_manager.find_relevant_context(
            query="",
            project_id=sample_chunks["project_id"]
        )

@pytest.mark.asyncio
async def test_invalid_project_id(context_manager):
    """Prueba el manejo de IDs de proyecto inválidos."""
    query = "¿Cómo funciona la autenticación?"
    invalid_project_id = uuid4()
    
    result = await context_manager.find_relevant_context(
        query=query,
        project_id=invalid_project_id
    )
    
    assert len(result) == 0, "No debe encontrar resultados para un proyecto inexistente"

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_context_manager_flow()) 