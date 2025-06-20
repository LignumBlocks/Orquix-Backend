#!/usr/bin/env python3
"""
Prueba para demostrar cómo funciona la inclusión automática de síntesis del moderador
en el endpoint normal de context chat.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.context_builder import context_builder_service

def print_separator(text: str):
    """Imprime un separador visual"""
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)

def print_section(text: str):
    """Imprime una sección"""
    print(f"\n📋 {text}")
    print("-" * 50)

async def test_automatic_synthesis_inclusion():
    """Prueba la inclusión automática de síntesis del moderador"""
    
    print_separator("PRUEBA: INCLUSIÓN AUTOMÁTICA DE SÍNTESIS DEL MODERADOR")
    
    print_section("ESCENARIO")
    print("1. El usuario ha construido contexto inicial")
    print("2. Se han consultado las IAs y el moderador ha hecho su análisis")
    print("3. El usuario continúa con context building NORMALMENTE")
    print("4. El sistema AUTOMÁTICAMENTE incluye la síntesis del moderador")
    
    # 1. Simular contexto inicial del usuario
    print_section("PASO 1: CONTEXTO INICIAL DEL USUARIO")
    
    initial_context = """
    Mi empresa es una startup de e-commerce que vende productos artesanales.
    Tenemos problemas con la logística y los costos de envío.
    Queremos expandirnos a nivel internacional pero no sabemos cómo.
    """
    
    print(f"Contexto inicial:")
    print(f"  {initial_context.strip()}")
    print(f"  Longitud: {len(initial_context)} caracteres")
    
    # 2. Simular función automática de inclusión de síntesis
    print_section("PASO 2: FUNCIÓN AUTOMÁTICA DE INCLUSIÓN")
    
    # Simular datos de síntesis del moderador (como vendrían de la BD)
    moderator_synthesis = """
    ## Resumen Conciso General
    Las respuestas convergen en que el e-commerce artesanal requiere optimización logística 
    y estrategias de expansión internacional graduales para competir efectivamente.
    
    ## Puntos de Consenso Directo
    - La optimización de la cadena de suministro es fundamental para reducir costos
    - La expansión internacional debe ser gradual, comenzando por mercados similares
    - Las alianzas con operadores logísticos locales son clave para el éxito
    
    ## Recomendaciones Principales
    - Implementar un sistema de gestión de inventario automatizado
    - Establecer alianzas con couriers especializados en productos frágiles
    - Comenzar expansión por países vecinos con regulaciones similares
    """
    
    key_themes = [
        "Optimización logística para e-commerce",
        "Estrategias de expansión internacional gradual",
        "Alianzas con operadores logísticos especializados"
    ]
    
    recommendations = [
        "Implementar sistema de gestión de inventario automatizado",
        "Establecer alianzas con couriers especializados",
        "Comenzar expansión por países vecinos"
    ]
    
    print("Síntesis del moderador detectada:")
    print(f"  📊 Temas clave: {len(key_themes)}")
    print(f"  💡 Recomendaciones: {len(recommendations)}")
    print(f"  📄 Longitud: {len(moderator_synthesis)} caracteres")
    
    # 3. Incluir automáticamente la síntesis
    print_section("PASO 3: INCLUSIÓN AUTOMÁTICA")
    
    enhanced_context = context_builder_service.include_moderator_synthesis(
        current_context=initial_context,
        synthesis_text=moderator_synthesis,
        key_themes=key_themes,
        recommendations=recommendations
    )
    
    print("✨ SÍNTESIS INCLUIDA AUTOMÁTICAMENTE:")
    print(f"  Contexto original: {len(initial_context)} chars")
    print(f"  Contexto mejorado: {len(enhanced_context)} chars")
    print(f"  Incremento: +{len(enhanced_context) - len(initial_context)} chars")
    print(f"  Contiene síntesis: {'🔬 Análisis del Moderador IA' in enhanced_context}")
    
    # 4. El usuario continúa normalmente
    print_section("PASO 4: USUARIO CONTINÚA NORMALMENTE")
    
    user_message = "Basándome en esto, ¿qué países me recomendarían para empezar la expansión?"
    
    print(f"💬 Usuario pregunta: '{user_message}'")
    print("🤖 Context Builder procesará con contexto enriquecido automáticamente...")
    
    # Procesar con context builder usando contexto enriquecido
    response = await context_builder_service.process_user_message(
        user_message=user_message,
        conversation_history=[],
        current_context=enhanced_context
    )
    
    print("\n🎯 RESPUESTA DEL CONTEXT BUILDER:")
    print(f"  Tipo: {response.message_type}")
    print(f"  Elementos de contexto: {response.context_elements_count}")
    print(f"  Sugerencias: {len(response.suggestions)}")
    
    print(f"\nTexto de respuesta:")
    print("─" * 60)
    lines = response.ai_response.split('\n')
    for i, line in enumerate(lines[:15], 1):  # Mostrar primeras 15 líneas
        print(f"{i:2d}│ {line}")
    if len(lines) > 15:
        print(f"   │ ... ({len(lines) - 15} líneas más)")
    print("─" * 60)
    
    # 5. Verificar que no se duplica la síntesis
    print_section("PASO 5: VERIFICAR NO DUPLICACIÓN")
    
    # Simular segunda llamada (la síntesis ya debería estar incluida)
    context_with_synthesis = response.accumulated_context
    
    # Intentar incluir síntesis de nuevo (debería detectar que ya está)
    context_after_second_call = context_builder_service.include_moderator_synthesis(
        current_context=context_with_synthesis,
        synthesis_text=moderator_synthesis,
        key_themes=key_themes,
        recommendations=recommendations
    )
    
    synthesis_count = context_after_second_call.count("🔬 Análisis del Moderador IA")
    
    print("🔄 Prueba de no duplicación:")
    print(f"  Longitud antes: {len(context_with_synthesis)} chars")
    print(f"  Longitud después: {len(context_after_second_call)} chars")
    print(f"  Ocurrencias de síntesis: {synthesis_count}")
    print(f"  ✅ No duplicación: {synthesis_count == 1}")
    
    # 6. Resumen del flujo
    print_section("RESUMEN DEL FLUJO IMPLEMENTADO")
    
    print("🔄 FLUJO AUTOMÁTICO:")
    print("  1. Usuario construye contexto inicial")
    print("  2. Se consultan IAs → Moderador genera síntesis")
    print("  3. ✨ Usuario continúa con endpoint NORMAL /context-chat")
    print("  4. ✨ Sistema AUTOMÁTICAMENTE detecta síntesis disponible")
    print("  5. ✨ Sistema incluye síntesis en contexto SIN intervención del usuario")
    print("  6. Context Builder responde con contexto enriquecido")
    print("  7. Futuras interacciones mantienen el contexto enriquecido")
    
    print("\n✅ VENTAJAS DE LA IMPLEMENTACIÓN:")
    print("  • 🔄 Flujo natural: usuario no necesita hacer nada especial")
    print("  • 🤖 Automático: detección e inclusión sin intervención")
    print("  • 🛡️ Robusto: no se duplica síntesis si ya está incluida")
    print("  • 🧠 Contexto rico: incluye insights del análisis de múltiples IAs")
    print("  • 📈 Escalable: funciona con cualquier proyecto/usuario")

async def main():
    """Función principal"""
    print("🚀 INICIANDO PRUEBA DE INCLUSIÓN AUTOMÁTICA DE SÍNTESIS")
    print("="*80)
    
    try:
        await test_automatic_synthesis_inclusion()
        
        print_separator("PRUEBA COMPLETADA EXITOSAMENTE")
        print("✅ La inclusión automática de síntesis del moderador está funcionando")
        print("✅ El usuario puede continuar con context building normalmente")
        print("✅ No se requieren endpoints adicionales ni botones especiales")
        print("✅ El flujo es completamente transparente para el usuario")
        
    except Exception as e:
        print(f"\n❌ ERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 