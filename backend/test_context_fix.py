#!/usr/bin/env python3
"""
Test simple para verificar el fix del context builder
"""

import asyncio
import sys
import os

# Añadir el directorio padre al path para importar los módulos
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.services.context_builder import ContextBuilderService

async def test_information_extraction():
    """Test de extracción de información completa"""
    print("🧪 Test: Extracción de información completa\n")
    
    service = ContextBuilderService()
    
    # Mensaje de prueba similar al del usuario
    test_message = "Tengo una startup que ofrece software de gestión para clínicas dentales. Estamos en fase beta y queremos crecer en México y Colombia."
    
    print(f"📝 Mensaje: {test_message}\n")
    
    # Test 1: Extracción de información con contexto vacío
    print("1️⃣ Extracción con contexto vacío:")
    extracted_info = await service._extract_information_from_message(test_message, "")
    print(f"   Información extraída: {extracted_info}\n")
    
    # Test 2: Actualización de contexto
    print("2️⃣ Actualización de contexto:")
    updated_context = service._update_accumulated_context("", extracted_info)
    print(f"   Contexto actualizado: {updated_context}\n")
    
    # Test 3: Segundo mensaje para ver acumulación
    second_message = "Necesitamos 100 clientes nuevos en los próximos 6 meses con un presupuesto de $10,000"
    print(f"📝 Segundo mensaje: {second_message}\n")
    
    print("3️⃣ Extracción del segundo mensaje:")
    extracted_info_2 = await service._extract_information_from_message(second_message, updated_context)
    print(f"   Información extraída: {extracted_info_2}\n")
    
    print("4️⃣ Contexto final acumulado:")
    final_context = service._update_accumulated_context(updated_context, extracted_info_2)
    print(f"   Contexto final: {final_context}\n")
    
    # Verificar que se mantiene información importante
    print("✅ Verificaciones:")
    checks = [
        ("Startup mencionada", "startup" in final_context.lower()),
        ("Software de gestión mencionado", "software" in final_context.lower() and "gestión" in final_context.lower()),
        ("Clínicas dentales mencionadas", "clínicas" in final_context.lower() and "dentales" in final_context.lower()),
        ("Fase beta mencionada", "beta" in final_context.lower()),
        ("Ubicaciones mencionadas", "méxico" in final_context.lower() and "colombia" in final_context.lower()),
        ("Objetivos numéricos incluidos", "100" in final_context or "6 meses" in final_context.lower()),
        ("Presupuesto incluido", "10,000" in final_context or "10000" in final_context)
    ]
    
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
    
    # Estadísticas finales
    word_count = len(final_context.split())
    char_count = len(final_context)
    print(f"\n📊 Estadísticas del contexto final:")
    print(f"   Caracteres: {char_count}")
    print(f"   Palabras: {word_count}")
    print(f"   Elementos: {service._count_context_elements(final_context)}")

async def main():
    """Función principal"""
    print("🔧 Test de Fix del Context Builder\n")
    print("=" * 50)
    
    await test_information_extraction()
    
    print("\n" + "=" * 50)
    print("🎯 Test completado!")

if __name__ == "__main__":
    asyncio.run(main()) 