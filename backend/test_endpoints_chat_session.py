"""
Test básico para verificar que los endpoints de Chat y Session funcionan correctamente.
"""
import asyncio
from uuid import uuid4, UUID
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_async_session
from app.crud.project import create_project
from app.schemas.project import ProjectCreate


async def test_endpoints_chat_session():
    """Test básico de endpoints Chat y Session."""
    
    print("🧪 Testeando endpoints de Chat y Session...")
    
    # Crear cliente de test
    client = TestClient(app)
    
    # Usuario mock
    mock_user_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # Headers de autenticación mock (usar token de desarrollo)
    headers = {
        "Authorization": "Bearer dev-mock-token-12345",
        "Content-Type": "application/json"
    }
    
    # Obtener sesión de base de datos para crear proyecto
    async for db in get_async_session():
        # Crear proyecto de prueba
        project_create = ProjectCreate(
            name="Proyecto Test Endpoints",
            description="Proyecto para probar endpoints Chat y Session",
            moderator_personality="analítico",
            moderator_temperature=0.7,
            moderator_length_penalty=1.0
        )
        project = await create_project(db, obj_in=project_create, user_id=UUID(mock_user_id))
        print(f"✅ Proyecto creado: {project.name} (ID: {project.id})")
        
        # Test 1: Crear chat
        print("\n📝 Test 1: Crear chat...")
        chat_data = {
            "project_id": str(project.id),
            "title": "Chat de Prueba Endpoints",
            "is_archived": False
        }
        
        response = client.post(
            f"/api/v1/projects/{project.id}/chats",
            json=chat_data,
            headers=headers
        )
        
        if response.status_code == 200:
            chat = response.json()
            chat_id = chat["id"]
            print(f"✅ Chat creado: {chat['title']} (ID: {chat_id})")
        else:
            print(f"❌ Error creando chat: {response.status_code} - {response.text}")
            return
        
        # Test 2: Obtener chat
        print("\n📖 Test 2: Obtener chat...")
        response = client.get(f"/api/v1/chats/{chat_id}", headers=headers)
        
        if response.status_code == 200:
            chat_retrieved = response.json()
            print(f"✅ Chat obtenido: {chat_retrieved['title']}")
        else:
            print(f"❌ Error obteniendo chat: {response.status_code} - {response.text}")
            return
        
        # Test 3: Listar chats del proyecto
        print("\n📋 Test 3: Listar chats del proyecto...")
        response = client.get(f"/api/v1/projects/{project.id}/chats", headers=headers)
        
        if response.status_code == 200:
            chats_list = response.json()
            print(f"✅ Chats listados: {chats_list['total']} total, {len(chats_list['chats'])} en página")
        else:
            print(f"❌ Error listando chats: {response.status_code} - {response.text}")
            return
        
        # Test 4: Crear sesión
        print("\n🔄 Test 4: Crear sesión...")
        session_data = {
            "chat_id": chat_id,
            "accumulated_context": "Contexto inicial de la sesión de prueba",
            "status": "active"
        }
        
        response = client.post(
            f"/api/v1/chats/{chat_id}/sessions",
            json=session_data,
            headers=headers
        )
        
        if response.status_code == 200:
            session = response.json()
            session_id = session["id"]
            print(f"✅ Sesión creada: {session_id} (orden: {session['order_index']})")
        else:
            print(f"❌ Error creando sesión: {response.status_code} - {response.text}")
            return
        
        # Test 5: Obtener sesión
        print("\n📖 Test 5: Obtener sesión...")
        response = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
        
        if response.status_code == 200:
            session_retrieved = response.json()
            print(f"✅ Sesión obtenida: {session_retrieved['status']}")
        else:
            print(f"❌ Error obteniendo sesión: {response.status_code} - {response.text}")
            return
        
        # Test 6: Listar sesiones del chat
        print("\n📋 Test 6: Listar sesiones del chat...")
        response = client.get(f"/api/v1/chats/{chat_id}/sessions", headers=headers)
        
        if response.status_code == 200:
            sessions_list = response.json()
            print(f"✅ Sesiones listadas: {sessions_list['total']} total")
        else:
            print(f"❌ Error listando sesiones: {response.status_code} - {response.text}")
            return
        
        # Test 7: Actualizar contexto de sesión
        print("\n✏️ Test 7: Actualizar contexto de sesión...")
        context_update = {
            "accumulated_context": "Contexto actualizado con nueva información"
        }
        
        response = client.put(
            f"/api/v1/sessions/{session_id}/context",
            json=context_update,
            headers=headers
        )
        
        if response.status_code == 200:
            session_updated = response.json()
            print(f"✅ Contexto actualizado: {len(session_updated['accumulated_context'])} caracteres")
        else:
            print(f"❌ Error actualizando contexto: {response.status_code} - {response.text}")
            return
        
        # Test 8: Obtener sesión activa
        print("\n🎯 Test 8: Obtener sesión activa...")
        response = client.get(f"/api/v1/chats/{chat_id}/active-session", headers=headers)
        
        if response.status_code == 200:
            active_session = response.json()
            print(f"✅ Sesión activa obtenida: {active_session['id']}")
        else:
            print(f"❌ Error obteniendo sesión activa: {response.status_code} - {response.text}")
            return
        
        # Test 9: Obtener cadena de contexto
        print("\n🔗 Test 9: Obtener cadena de contexto...")
        response = client.get(f"/api/v1/sessions/{session_id}/context-chain", headers=headers)
        
        if response.status_code == 200:
            context_chain = response.json()
            print(f"✅ Cadena de contexto: {context_chain['sessions_count']} sesiones, {context_chain['total_context_length']} caracteres")
        else:
            print(f"❌ Error obteniendo cadena de contexto: {response.status_code} - {response.text}")
            return
        
        # Test 10: Chat con sesiones
        print("\n🔗 Test 10: Chat con sesiones...")
        response = client.get(f"/api/v1/chats/{chat_id}/with-sessions", headers=headers)
        
        if response.status_code == 200:
            chat_with_sessions = response.json()
            print(f"✅ Chat con sesiones: {len(chat_with_sessions['sessions'])} sesiones incluidas")
        else:
            print(f"❌ Error obteniendo chat con sesiones: {response.status_code} - {response.text}")
            return
        
        print("\n🎉 ¡Todos los tests de endpoints completados exitosamente!")
        break


def main():
    """Ejecutar test de endpoints."""
    print("🚀 Iniciando tests de endpoints Chat y Session...\n")
    asyncio.run(test_endpoints_chat_session())


if __name__ == "__main__":
    main() 