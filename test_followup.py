#!/usr/bin/env python3
"""
Script de prueba para diagnosticar el FollowUpInterpreter
"""
import asyncio
import sys
import os

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.followup_interpreter import FollowUpInterpreter

def test_heuristic_patterns():
    """Probar los patrones heurísticos directamente"""
    interpreter = FollowUpInterpreter(None)  # Sin DB para esta prueba
    
    test_cases = [
        "¿Qué algoritmos utilizar?",
        "¿Y si vamos con niños?",
        "Mejora eso",
        "Dame más detalles",
        "Otra opción sería...",
        "También considera",
        "Nueva consulta: necesito ayuda con Python"
    ]
    
    print("🔍 PRUEBA DE PATRONES HEURÍSTICOS")
    print("=" * 50)
    
    for prompt in test_cases:
        result = interpreter._analyze_heuristic_patterns(prompt)
        print(f"\nPrompt: '{prompt}'")
        print(f"  ✓ Es continuación: {result['is_continuation']}")
        print(f"  ✓ Tipo: {result['reference_type']}")
        print(f"  ✓ Confianza: {result['confidence']}")
        print(f"  ✓ Keywords: {result['keywords']}")

if __name__ == "__main__":
    test_heuristic_patterns() 