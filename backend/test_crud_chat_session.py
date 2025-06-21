"""
Test básico para verificar que los CRUDs de Chat y Session funcionan correctamente.
"""
import asyncio
from uuid import uuid4, UUID
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_async_session, create_db_and_tables
from app.crud.chat import create_chat, get_chat, get_chats_by_project
from app.crud.session import create_session, get_session, get_sessions_by_chat, get_active_session
from app.crud.project import get_projects_by_user, create_project
from app.schemas.project import ProjectCreate


async def test_crud_chat_session():
    """Test básico de CRUD para Chat y Session."""
    
    print("🔧 Inicializando base de datos...")
    await create_db_and_tables()
    
    # Obtener sesión de base de datos
    async for db in get_async_session():
        print("📊 Conectado a la base de datos")
        
        # Usar el usuario mock existente
        mock_user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        
        # Crear un proyecto de prueba
        project_create = ProjectCreate(
            name="Proyecto Test CRUD",
            description="Proyecto para probar CRUDs de Chat y Session",
            moderator_personality="analítico",
            moderator_temperature=0.7,
            moderator_length_penalty=1.0
        )
        project = await create_project(db, obj_in=project_create, user_id=mock_user_id)
        print(f"✅ Proyecto creado: {project.name} (ID: {project.id})")
        
        # Crear un chat
        print("\n📝 Creando chat...")
        chat = await create_chat(
            db=db,
            project_id=project.id,
            user_id=mock_user_id,
            title="Chat de Prueba CRUD"
        )
        print(f"✅ Chat creado: {chat.title} (ID: {chat.id})")
        
        # Verificar que se puede obtener el chat
        retrieved_chat = await get_chat(db, chat.id)
        print(f"✅ Chat recuperado: {retrieved_chat.title}")
        
        # Obtener chats del proyecto
        project_chats = await get_chats_by_project(db, project.id)
        print(f"✅ Chats en el proyecto: {len(project_chats)}")
        
        # Crear primera sesión
        print("\n🔄 Creando primera sesión...")
        session1 = await create_session(
            db=db,
            chat_id=chat.id,
            user_id=mock_user_id,
            accumulated_context="Contexto inicial de la primera sesión",
            status="active"
        )
        print(f"✅ Primera sesión creada: {session1.id} (orden: {session1.order_index})")
        
        # Crear segunda sesión
        print("\n🔄 Creando segunda sesión...")
        session2 = await create_session(
            db=db,
            chat_id=chat.id,
            user_id=mock_user_id,
            accumulated_context="Contexto acumulado de la segunda sesión",
            status="active"
        )
        print(f"✅ Segunda sesión creada: {session2.id} (orden: {session2.order_index})")
        print(f"✅ Sesión anterior: {session2.previous_session_id}")
        
        # Verificar que la segunda sesión apunta a la primera
        if session2.previous_session_id == session1.id:
            print("✅ Relación de sesiones correcta")
        else:
            print("❌ Error en relación de sesiones")
        
        # Obtener sesiones del chat
        chat_sessions = await get_sessions_by_chat(db, chat.id)
        print(f"✅ Sesiones en el chat: {len(chat_sessions)}")
        
        # Obtener sesión activa
        active_session = await get_active_session(db, chat.id)
        print(f"✅ Sesión activa: {active_session.id if active_session else 'Ninguna'}")
        
        # Verificar orden de sesiones
        for i, session in enumerate(chat_sessions):
            print(f"   Sesión {i+1}: ID={session.id}, orden={session.order_index}")
        
        print("\n🎉 ¡Test de CRUD completado exitosamente!")
        break


if __name__ == "__main__":
    asyncio.run(test_crud_chat_session()) 