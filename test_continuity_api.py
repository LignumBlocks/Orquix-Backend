#!/usr/bin/env python3
"""
Script para probar la continuidad conversacional simplificada a través del API HTTP.
"""

import requests
import json
import time
from uuid import uuid4

# Configuración
BASE_URL = "http://localhost:8000/api/v1"
PROJECT_ID = "c9cc165a-6fed-4134-bf20-0e5897e3b7c8"  # ID de proyecto real del log

# Headers para autenticación (simulada)
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer fake-token-for-testing"
}

def test_conversation_modes():
    """Prueba los diferentes modos de conversación"""
    
    print("🧪 PRUEBA: Continuidad Conversacional Simplificada via API")
    print("=" * 60)
    
    # PASO 1: Crear primera consulta para establecer contexto
    print("\n📝 PASO 1: Crear contexto inicial")
    print("-" * 40)
    
    first_query = {
        "user_prompt_text": "Necesito hacer un MVP para resumir noticias de internet",
        "include_context": True,
        "conversation_mode": "new"  # Forzar como nueva conversación
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/projects/{PROJECT_ID}/query",
            headers=HEADERS,
            json=first_query,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Primera consulta exitosa")
            print(f"   ID: {result['interaction_event_id']}")
            print(f"   Síntesis: {result['synthesis_text'][:100]}...")
        else:
            print(f"❌ Error en primera consulta: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return
    
    # Esperar un poco para que se guarde la interacción
    print("\n⏳ Esperando 2 segundos para que se guarde la interacción...")
    time.sleep(2)
    
    # PASO 2: Probar los diferentes modos de conversación
    print("\n📝 PASO 2: Probar modos de conversación")
    print("-" * 40)
    
    follow_up_prompt = "¿Qué algoritmos utilizar?"
    
    for mode in ["auto", "continue", "new"]:
        print(f"\n🔍 Probando modo: '{mode}'")
        
        query = {
            "user_prompt_text": follow_up_prompt,
            "include_context": True,
            "conversation_mode": mode
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/projects/{PROJECT_ID}/query",
                headers=HEADERS,
                json=query,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Éxito - ID: {result['interaction_event_id']}")
                
                # Verificar si hay indicios de continuidad en la respuesta
                synthesis = result['synthesis_text']
                if any(word in synthesis.lower() for word in ['mvp', 'noticias', 'resumir', 'anterior', 'contexto']):
                    print(f"   🔗 CONTINUIDAD DETECTADA - La respuesta menciona el contexto previo")
                else:
                    print(f"   🆕 TEMA NUEVO - La respuesta no parece usar contexto previo")
                    
                print(f"   📝 Síntesis: {synthesis[:150]}...")
                
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   📄 Respuesta: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Error de conexión: {e}")
    
    # PASO 3: Verificar estado de conversación
    print("\n📝 PASO 3: Verificar estado de conversación")
    print("-" * 40)
    
    try:
        response = requests.get(
            f"{BASE_URL}/projects/{PROJECT_ID}/conversation-state",
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            state = response.json()
            print(f"✅ Estado de conversación obtenido")
            print(f"   📊 Total interacciones: {state.get('total_interactions', 'N/A')}")
            print(f"   🕒 Última interacción: {state.get('last_interaction_time', 'N/A')}")
            print(f"   🔗 Continuidad disponible: {state.get('has_context', 'N/A')}")
        else:
            print(f"❌ Error obteniendo estado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    test_conversation_modes() 