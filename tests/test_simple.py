import pytest
from uuid import uuid4
from sqlmodel import Session, create_engine
from sqlalchemy import text
from app.core.config import settings

def test_import_context_manager():
    """Prueba básica de importación"""
    from app.services.context_manager import ContextManager
    assert ContextManager is not None

def test_database_connection():
    """Prueba básica de conexión a base de datos"""
    try:
        database_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
        engine = create_engine(database_url, echo=False)
        with Session(engine) as session:
            result = session.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        print("✅ Conexión a base de datos exitosa")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        raise

def test_openai_config():
    """Verificar que la configuración de OpenAI está presente"""
    assert hasattr(settings, 'OPENAI_API_KEY')
    assert settings.OPENAI_API_KEY is not None
    assert len(settings.OPENAI_API_KEY) > 0
    print("✅ API Key de OpenAI configurada")

if __name__ == "__main__":
    test_import_context_manager()
    test_database_connection()
    test_openai_config()
    print("✅ Todas las pruebas básicas pasaron") 