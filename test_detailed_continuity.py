#!/usr/bin/env python3
"""
Script detallado para probar continuidad conversacional con información completa de debugging.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
PROJECT_ID = "c9cc165a-6fed-4134-bf20-0e5897e3b7c8"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer fake-token-for-testing"
}

def print_separator(title):
    """Imprimir separador visual"""
    print("\n" + "="*80)
    print(f"🔍 {title}")
    print("="*80)

def print_json_pretty(data, title=""):
    """Imprimir JSON de forma legible"""
    if title:
        print(f"\n📋 {title}:")
    print("-" * 60)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("-" * 60)

def make_detailed_query(prompt, mode="auto", step_number=1):
    """Hacer una consulta detallada al API con información completa"""
    print_separator(f"PASO {step_number}: {prompt[:50]}...")
    
    query = {
        "user_prompt_text": prompt,
        "include_context": True,
        "conversation_mode": mode
    }
    
    print(f"📤 Enviando consulta:")
    print(f"   • Prompt: '{prompt}'")
    print(f"   • Modo: {mode}")
    print(f"   • Timestamp: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        print(f"\n⏳ Haciendo petición a: {BASE_URL}/projects/{PROJECT_ID}/query")
        response = requests.post(
            f"{BASE_URL}/projects/{PROJECT_ID}/query",
            headers=HEADERS,
            json=query,
            timeout=60
        )
        
        print(f"📥 Respuesta recibida - Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Información básica
            print(f"\n✅ CONSULTA EXITOSA")
            print(f"   • ID Interacción: {result.get('interaction_event_id', 'N/A')}")
            print(f"   • Timestamp: {result.get('timestamp', 'N/A')}")
            
            # Información de continuidad
            continuity_info = result.get('continuity_analysis', {})
            if continuity_info:
                print(f"\n🧠 ANÁLISIS DE CONTINUIDAD:")
                print(f"   • Es continuación: {continuity_info.get('is_continuation', 'N/A')}")
                print(f"   • Tipo de referencia: {continuity_info.get('reference_type', 'N/A')}")
                print(f"   • Puntuación confianza: {continuity_info.get('confidence_score', 'N/A')}")
                print(f"   • ID interacción previa: {continuity_info.get('previous_interaction_id', 'N/A')}")
                print(f"   • Palabras clave contextuales: {continuity_info.get('contextual_keywords', [])}")
            else:
                print(f"\n❌ NO SE ENCONTRÓ INFORMACIÓN DE CONTINUIDAD")
            
            # Contexto utilizado
            context_used = result.get('context_used', {})
            if context_used:
                print(f"\n📚 CONTEXTO UTILIZADO:")
                print(f"   • Número de documentos: {len(context_used.get('documents', []))}")
                print(f"   • Interacciones previas: {len(context_used.get('previous_interactions', []))}")
                
                # Mostrar documentos de contexto
                for i, doc in enumerate(context_used.get('documents', [])[:3]):  # Solo primeros 3
                    print(f"   • Doc {i+1}: {doc.get('content', '')[:100]}...")
                
                # Mostrar interacciones previas
                for i, interaction in enumerate(context_used.get('previous_interactions', [])[:2]):  # Solo primeras 2
                    print(f"   • Interacción previa {i+1}:")
                    print(f"     - Prompt: {interaction.get('user_prompt_text', '')[:80]}...")
                    print(f"     - Síntesis: {interaction.get('moderated_synthesis', '')[:80]}...")
            else:
                print(f"\n❌ NO SE ENCONTRÓ CONTEXTO UTILIZADO")
            
            # Respuestas de las IAs
            ai_responses = result.get('ai_responses', [])
            print(f"\n🤖 RESPUESTAS DE IAS ({len(ai_responses)} total):")
            for i, response in enumerate(ai_responses[:2]):  # Solo primeras 2
                provider = response.get('provider_name', 'Unknown')
                content = response.get('response_text', '')[:150]
                print(f"   • {provider}: {content}...")
            
            # Síntesis final
            synthesis = result.get('synthesis_text', '')
            print(f"\n📝 SÍNTESIS FINAL:")
            print(f"   • Longitud: {len(synthesis)} caracteres")
            print(f"   • Contenido: {synthesis[:200]}...")
            
            # Análisis de palabras clave en la síntesis
            context_keywords = ['mvp', 'noticias', 'resumir', 'algoritmos', 'frontend', 'anterior', 'contexto', 'previo']
            found_keywords = [word for word in context_keywords if word in synthesis.lower()]
            print(f"\n🔍 PALABRAS CLAVE ENCONTRADAS EN SÍNTESIS:")
            print(f"   • Encontradas: {found_keywords}")
            print(f"   • No encontradas: {[word for word in context_keywords if word not in found_keywords]}")
            
            return result
            
        else:
            print(f"❌ ERROR {response.status_code}")
            print(f"   • Mensaje: {response.text[:300]}")
            return None
            
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {str(e)}")
        return None

def test_followup_interpreter_directly():
    """Probar el FollowUpInterpreter directamente"""
    print_separator("PRUEBA DIRECTA DEL FOLLOWUP INTERPRETER")
    
    test_data = {
        "current_prompt": "¿Qué algoritmos utilizar?",
        "project_id": PROJECT_ID
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/followup/analyze",
            headers=HEADERS,
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print_json_pretty(result, "Resultado del FollowUpInterpreter")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error probando FollowUpInterpreter: {e}")

def main():
    print("🧪 PRUEBA DETALLADA: Continuidad Conversacional")
    print("🎯 Objetivo: Analizar en detalle qué encuentra y no encuentra el sistema")
    
    # PASO 1: Primera consulta (establecer contexto)
    result1 = make_detailed_query(
        "Necesito hacer un MVP para resumir noticias usando IA", 
        "new", 
        1
    )
    
    if not result1:
        print("❌ Primera consulta falló - Abortando prueba")
        return
    
    # Esperar para que se guarde
    print(f"\n⏳ Esperando 5 segundos para que se guarde el contexto...")
    time.sleep(5)
    
    # Probar FollowUpInterpreter directamente
    test_followup_interpreter_directly()
    
    # PASO 2: Segunda consulta con modo AUTO
    result2 = make_detailed_query(
        "¿Qué algoritmos de machine learning recomiendas?", 
        "auto", 
        2
    )
    
    # PASO 3: Tercera consulta con modo CONTINUE
    result3 = make_detailed_query(
        "¿Y para el frontend de este MVP?", 
        "continue", 
        3
    )
    
    # PASO 4: Cuarta consulta muy explícita
    result4 = make_detailed_query(
        "Mejora la propuesta anterior del MVP de noticias", 
        "auto", 
        4
    )
    
    print_separator("RESUMEN FINAL")
    print("✅ Prueba completada")
    print("📊 Revisa los detalles arriba para entender el comportamiento del sistema")

if __name__ == "__main__":
    main() 