#!/usr/bin/env python3
"""
Test script para verificar la nueva arquitectura de sesiones.
Prueba los endpoints corregidos que siguen la jerarquía: Proyecto -> Chat -> Sesiones
"""

import requests
import json
from uuid import uuid4

# Configuración
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer dev-mock-token-12345"
}

def test_new_session_architecture():
    print("🧪 Probando nueva arquitectura de sesiones")
    print("=" * 60)
    
    # 1. Obtener proyectos
    print("\n📋 1. Obteniendo proyectos...")
    response = requests.get(f"{BASE_URL}/projects/", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Error obteniendo proyectos: {response.status_code}")
        return
    
    projects = response.json()
    if not projects:
        print("❌ No hay proyectos disponibles")
        return
    
    project_id = projects[0]["id"]
    print(f"✅ Usando proyecto: {project_id}")
    
    # 2. Obtener chats del proyecto
    print(f"\n💬 2. Obteniendo chats del proyecto {project_id}...")
    response = requests.get(f"{BASE_URL}/projects/{project_id}/chats", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Error obteniendo chats: {response.status_code}")
        return
    
    chats_data = response.json()
    chats = chats_data.get("chats", [])
    
    if not chats:
        print("⚠️ No hay chats, creando uno nuevo...")
        # Crear chat
        chat_data = {
            "title": "Test Chat para Sesiones"
        }
        response = requests.post(f"{BASE_URL}/projects/{project_id}/chats", 
                               json=chat_data, headers=HEADERS)
        if response.status_code != 200:
            print(f"❌ Error creando chat: {response.status_code}")
            return
        
        chat = response.json()
        chat_id = chat["id"]
        print(f"✅ Chat creado: {chat_id}")
    else:
        chat_id = chats[0]["id"]
        print(f"✅ Usando chat existente: {chat_id}")
    
    # 3. Crear sesiones en el chat
    print(f"\n🔄 3. Creando sesiones en el chat {chat_id}...")
    
    # Crear primera sesión
    session1_data = {
        "accumulated_context": "Primera sesión de prueba con contexto inicial",
        "status": "active"
    }
    response = requests.post(f"{BASE_URL}/chats/{chat_id}/sessions", 
                           json=session1_data, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Error creando primera sesión: {response.status_code}")
        return
    
    session1 = response.json()
    print(f"✅ Primera sesión creada: {session1['id']}")
    
    # Completar primera sesión
    status_data = {
        "status": "completed",
        "final_question": "¿Qué opinas sobre esto?"
    }
    response = requests.put(f"{BASE_URL}/sessions/{session1['id']}/status", 
                          json=status_data, headers=HEADERS)
    if response.status_code == 200:
        print(f"✅ Primera sesión marcada como completada")
    
    # Crear segunda sesión (debería heredar contexto)
    session2_data = {
        "accumulated_context": "",  # Vacío para probar herencia
        "status": "active"
    }
    response = requests.post(f"{BASE_URL}/chats/{chat_id}/sessions", 
                           json=session2_data, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Error creando segunda sesión: {response.status_code}")
        return
    
    session2 = response.json()
    print(f"✅ Segunda sesión creada: {session2['id']}")
    print(f"📝 Contexto heredado: {len(session2.get('accumulated_context', ''))} caracteres")
    
    # 4. Probar endpoint de sesiones detalladas del chat
    print(f"\n📊 4. Probando endpoint de sesiones detalladas...")
    response = requests.get(f"{BASE_URL}/chats/{chat_id}/sessions/detailed", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Error obteniendo sesiones detalladas: {response.status_code}")
        return
    
    detailed_sessions = response.json()
    print(f"✅ Sesiones detalladas obtenidas:")
    print(f"   - Chat: {detailed_sessions['chat_title']}")
    print(f"   - Total sesiones: {detailed_sessions['total_sessions']}")
    print(f"   - Sesión activa: {detailed_sessions['active_session_id']}")
    print(f"   - Sesiones completadas: {detailed_sessions['completed_sessions']}")
    
    # 5. Probar endpoint de resumen de proyecto
    print(f"\n📈 5. Probando endpoint de resumen del proyecto...")
    response = requests.get(f"{BASE_URL}/context-chat/projects/{project_id}/context-sessions-summary", 
                          headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Error obteniendo resumen del proyecto: {response.status_code}")
        return
    
    project_summary = response.json()
    print(f"✅ Resumen del proyecto obtenido:")
    print(f"   - Total chats: {project_summary['total_chats']}")
    print(f"   - Total sesiones: {project_summary['total_sessions']}")
    print(f"   - Sesiones activas: {project_summary['active_sessions']}")
    
    for chat_info in project_summary['chats_with_sessions']:
        print(f"   - Chat '{chat_info['chat_title']}': {chat_info['sessions_count']} sesiones")
    
    # 6. Verificar herencia de contexto
    print(f"\n🔗 6. Verificando herencia de contexto...")
    if session2.get('accumulated_context') and session1['accumulated_context'] in session2['accumulated_context']:
        print("✅ Herencia de contexto funcionando correctamente")
    else:
        print("⚠️ La herencia de contexto puede no estar funcionando como esperado")
    
    print(f"\n🎉 ¡Prueba de arquitectura completada exitosamente!")
    print("=" * 60)
    
    return {
        "project_id": project_id,
        "chat_id": chat_id,
        "session1_id": session1['id'],
        "session2_id": session2['id']
    }

if __name__ == "__main__":
    try:
        result = test_new_session_architecture()
        print(f"\n📋 Resultado final: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Error en la prueba: {e}") 