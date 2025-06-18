#!/usr/bin/env python3
"""
Script simple para probar continuidad conversacional paso a paso.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
PROJECT_ID = "c9cc165a-6fed-4134-bf20-0e5897e3b7c8"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer fake-token-for-testing"
}

def make_query(prompt, mode="auto"):
    """Hacer una consulta al API"""
    query = {
        "user_prompt_text": prompt,
        "include_context": True,
        "conversation_mode": mode
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/projects/{PROJECT_ID}/query",
            headers=HEADERS,
            json=query,
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print(f"❌ Error {response.status_code}: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("🧪 PRUEBA SIMPLE: Continuidad Conversacional")
    print("=" * 50)
    
    # PASO 1: Primera consulta (establecer contexto)
    print("\n📝 PASO 1: Establecer contexto inicial")
    result1 = make_query("Necesito hacer un MVP para resumir noticias", "new")
    if result1:
        print(f"✅ Primera consulta exitosa - ID: {result1['interaction_event_id']}")
        print(f"📝 Síntesis: {result1['synthesis_text'][:100]}...")
    else:
        print("❌ Primera consulta falló")
        return
    
    # Esperar para que se guarde
    print("\n⏳ Esperando 3 segundos...")
    time.sleep(3)
    
    # PASO 2: Segunda consulta con modo AUTO (debería detectar continuidad)
    print("\n📝 PASO 2: Segunda consulta - Modo AUTO")
    result2 = make_query("¿Qué algoritmos utilizar?", "auto")
    if result2:
        print(f"✅ Segunda consulta exitosa - ID: {result2['interaction_event_id']}")
        synthesis = result2['synthesis_text']
        
        # Verificar si menciona el contexto previo
        context_words = ['mvp', 'noticias', 'resumir', 'anterior', 'contexto', 'previo']
        has_context = any(word in synthesis.lower() for word in context_words)
        
        if has_context:
            print("🔗 ¡CONTINUIDAD DETECTADA! - La respuesta usa contexto previo")
        else:
            print("🆕 Tema nuevo - No se detectó continuidad")
            
        print(f"📝 Síntesis: {synthesis[:150]}...")
    else:
        print("❌ Segunda consulta falló")
    
    # PASO 3: Tercera consulta con modo CONTINUE (forzar continuidad)
    print("\n📝 PASO 3: Tercera consulta - Modo CONTINUE")
    result3 = make_query("¿Y para el frontend?", "continue")
    if result3:
        print(f"✅ Tercera consulta exitosa - ID: {result3['interaction_event_id']}")
        synthesis = result3['synthesis_text']
        
        context_words = ['mvp', 'noticias', 'resumir', 'frontend', 'anterior']
        has_context = any(word in synthesis.lower() for word in context_words)
        
        if has_context:
            print("🔗 ¡CONTINUIDAD FORZADA! - La respuesta usa contexto previo")
        else:
            print("🆕 Sin contexto - Modo continue no funcionó")
            
        print(f"📝 Síntesis: {synthesis[:150]}...")
    else:
        print("❌ Tercera consulta falló")

if __name__ == "__main__":
    main() 