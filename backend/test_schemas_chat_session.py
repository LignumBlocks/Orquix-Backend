"""
Test básico para verificar que los schemas de Chat y Session funcionan correctamente.
"""
import asyncio
from uuid import uuid4, UUID
from datetime import datetime
from pydantic import ValidationError

from app.schemas.chat import (
    ChatCreate, ChatUpdate, ChatResponse, ChatSummary, 
    ChatWithSessions, ChatStats, ChatListResponse
)
from app.schemas.session import (
    SessionCreate, SessionUpdate, SessionResponse, SessionSummary,
    SessionWithContext, SessionContextChain, SessionStats,
    SessionStatusUpdate, SessionContextUpdate
)


def test_chat_schemas():
    """Test de schemas de Chat."""
    print("🧪 Testeando schemas de Chat...")
    
    # Test ChatCreate
    chat_create = ChatCreate(
        project_id=uuid4(),
        title="Chat de Prueba",
        is_archived=False
    )
    print(f"✅ ChatCreate: {chat_create.title}")
    
    # Test ChatUpdate
    chat_update = ChatUpdate(
        title="Nuevo Título",
        is_archived=True
    )
    print(f"✅ ChatUpdate: {chat_update.title}")
    
    # Test ChatResponse
    chat_response = ChatResponse(
        id=uuid4(),
        project_id=uuid4(),
        user_id=uuid4(),
        title="Chat Respuesta",
        is_archived=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    print(f"✅ ChatResponse: {chat_response.id}")
    
    # Test ChatSummary
    chat_summary = ChatSummary(
        id=uuid4(),
        title="Chat Resumen",
        is_archived=False,
        created_at=datetime.now(),
        sessions_count=3,
        last_activity=datetime.now()
    )
    print(f"✅ ChatSummary: {chat_summary.sessions_count} sesiones")
    
    # Test ChatStats
    chat_stats = ChatStats(
        chat_id=uuid4(),
        total_sessions=5,
        active_sessions=2,
        completed_sessions=3,
        total_interactions=15,
        total_context_length=2500,
        first_session_date=datetime.now(),
        last_session_date=datetime.now()
    )
    print(f"✅ ChatStats: {chat_stats.total_sessions} sesiones, {chat_stats.total_interactions} interacciones")
    
    # Test validación de errores
    try:
        ChatCreate(project_id="invalid-uuid", title="")
        print("❌ Error: debería haber fallado la validación")
    except ValidationError:
        print("✅ Validación de errores funciona correctamente")
    
    print("🎉 Todos los schemas de Chat funcionan correctamente\n")


def test_session_schemas():
    """Test de schemas de Session."""
    print("🧪 Testeando schemas de Session...")
    
    # Test SessionCreate
    session_create = SessionCreate(
        chat_id=uuid4(),
        accumulated_context="Contexto inicial",
        status="active"
    )
    print(f"✅ SessionCreate: {session_create.status}")
    
    # Test SessionUpdate
    session_update = SessionUpdate(
        accumulated_context="Contexto actualizado",
        final_question="¿Cuál es la conclusión?",
        status="completed"
    )
    print(f"✅ SessionUpdate: {session_update.status}")
    
    # Test SessionResponse
    session_response = SessionResponse(
        id=uuid4(),
        chat_id=uuid4(),
        previous_session_id=uuid4(),
        user_id=uuid4(),
        accumulated_context="Contexto de respuesta",
        final_question="Pregunta final",
        status="completed",
        order_index=1,
        started_at=datetime.now(),
        finished_at=datetime.now()
    )
    print(f"✅ SessionResponse: orden {session_response.order_index}")
    
    # Test SessionSummary
    session_summary = SessionSummary(
        id=uuid4(),
        order_index=2,
        status="active",
        started_at=datetime.now(),
        context_length=1500,
        interactions_count=5,
        has_final_question=True
    )
    print(f"✅ SessionSummary: {session_summary.interactions_count} interacciones")
    
    # Test SessionWithContext
    session_with_context = SessionWithContext(
        id=uuid4(),
        chat_id=uuid4(),
        accumulated_context="Contexto completo muy largo...",
        status="active",
        order_index=1,
        started_at=datetime.now(),
        context_preview="Contexto completo muy...",
        context_word_count=250,
        context_sections=["Introducción", "Desarrollo", "Conclusión"]
    )
    print(f"✅ SessionWithContext: {session_with_context.context_word_count} palabras")
    
    # Test SessionContextChain
    session_chain = SessionContextChain(
        session_id=uuid4(),
        context_chain=[session_response],
        total_context_length=3000,
        sessions_count=3
    )
    print(f"✅ SessionContextChain: {session_chain.sessions_count} sesiones")
    
    # Test SessionStats
    session_stats = SessionStats(
        session_id=uuid4(),
        interactions_count=8,
        context_length=2000,
        context_word_count=400,
        processing_time_total=15000,
        ai_responses_count=16,
        duration_minutes=25.5
    )
    print(f"✅ SessionStats: {session_stats.duration_minutes} minutos")
    
    # Test schemas de actualización específicos
    status_update = SessionStatusUpdate(
        status="completed",
        final_question="¿Qué aprendimos?"
    )
    print(f"✅ SessionStatusUpdate: {status_update.status}")
    
    context_update = SessionContextUpdate(
        accumulated_context="Nuevo contexto acumulado completo"
    )
    print(f"✅ SessionContextUpdate: {len(context_update.accumulated_context)} caracteres")
    
    print("🎉 Todos los schemas de Session funcionan correctamente\n")


def test_complex_schemas():
    """Test de schemas complejos y casos edge."""
    print("🧪 Testeando schemas complejos...")
    
    # Test ChatWithSessions (con lista vacía)
    chat_with_sessions = ChatWithSessions(
        id=uuid4(),
        project_id=uuid4(),
        user_id=uuid4(),
        title="Chat con Sesiones",
        is_archived=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        sessions=[]  # Lista vacía por defecto
    )
    print(f"✅ ChatWithSessions: {len(chat_with_sessions.sessions)} sesiones")
    
    # Test valores por defecto
    session_base = SessionCreate(chat_id=uuid4())
    assert session_base.accumulated_context == ""
    assert session_base.status == "active"
    print("✅ Valores por defecto funcionan correctamente")
    
    # Test campos opcionales
    minimal_chat = ChatResponse(
        id=uuid4(),
        project_id=uuid4(),
        title="Chat Mínimo",
        is_archived=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
        # user_id y deleted_at son opcionales
    )
    assert minimal_chat.user_id is None
    print("✅ Campos opcionales funcionan correctamente")
    
    print("🎉 Schemas complejos funcionan correctamente\n")


def main():
    """Ejecutar todos los tests."""
    print("🚀 Iniciando tests de schemas Chat y Session...\n")
    
    test_chat_schemas()
    test_session_schemas()
    test_complex_schemas()
    
    print("🎊 ¡Todos los tests de schemas completados exitosamente!")


if __name__ == "__main__":
    main() 