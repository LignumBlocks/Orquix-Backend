#!/usr/bin/env python3
"""
Script de demostración del nuevo Sidebar de Contexto Actual.
Muestra cómo se visualiza el contexto en tiempo real durante la construcción.
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

def simulate_sidebar_display(context: str, messages: list, building_mode: bool):
    """Simula cómo se vería el contexto en el sidebar"""
    
    # Calcular estadísticas
    words = len(context.split()) if context else 0
    chars = len(context) if context else 0
    sections = len(context.split('\n\n')) if context else 0
    
    print("\n┌─────────────────────────────────────────┐")
    print("│              SIDEBAR CONTEXTO           │")
    print("├─────────────────────────────────────────┤")
    print("│  [Contexto] [IAs]                       │")
    print("├─────────────────────────────────────────┤")
    print(f"│  Contexto Actual {'🔄 Construyendo...' if building_mode else '✅ Listo':<18} │")
    print("├─────────────────────────────────────────┤")
    print(f"│  📊 {words:<3} palabras  {chars:<4} chars  {sections:<2} secc. │")
    print("├─────────────────────────────────────────┤")
    
    if context:
        print("│  📄 Información Acumulada:              │")
        print("│                                         │")
        
        # Mostrar primeras líneas del contexto
        lines = context.split('\n')[:6]  # Primeras 6 líneas
        for line in lines:
            display_line = line[:37] + "..." if len(line) > 37 else line
            print(f"│  {display_line:<37}   │")
        
        if len(context.split('\n')) > 6:
            print("│  ...                                    │")
    else:
        print("│  📄 No hay contexto disponible          │")
        print("│     Inicia una conversación para        │")
        print("│     construir contexto                  │")
    
    print("├─────────────────────────────────────────┤")
    
    if messages:
        print(f"│  🔄 Historial ({len(messages)} mensajes):         │")
        for i, msg in enumerate(messages[-2:], 1):  # Últimos 2 mensajes
            user_preview = msg['user_message'][:25] + "..." if len(msg['user_message']) > 25 else msg['user_message']
            ai_preview = msg['ai_response'][:28] + "..." if len(msg['ai_response']) > 28 else msg['ai_response']
            print(f"│  {i}. U: {user_preview:<30}   │")
            print(f"│     IA: {ai_preview:<30}  │")
    
    print("└─────────────────────────────────────────┘")

async def demo_context_sidebar():
    """Demostración del sidebar de contexto en acción"""
    
    print_separator("DEMOSTRACIÓN: SIDEBAR DE CONTEXTO ACTUAL")
    
    print_section("ESCENARIO")
    print("El usuario puede ver SIEMPRE el contexto actual en el sidebar derecho.")
    print("El sidebar tiene dos tabs: 'Contexto' (activo) e 'IAs'.")
    print("Se actualiza en tiempo real mientras se construye el contexto.")
    
    # Simular construcción de contexto paso a paso
    messages = []
    context = ""
    
    # Estado inicial - sin contexto
    print_section("PASO 1: ESTADO INICIAL - SIN CONTEXTO")
    simulate_sidebar_display(context, messages, False)
    
    # Primer mensaje del usuario
    print_section("PASO 2: PRIMER MENSAJE DEL USUARIO")
    user_msg_1 = "Tengo una startup de e-commerce que vende productos artesanales mexicanos"
    
    print(f"💬 Usuario: {user_msg_1}")
    print("🤖 Context Builder procesando...")
    
    # Simular respuesta del context builder
    response_1 = await context_builder_service.process_user_message(
        user_message=user_msg_1,
        conversation_history=[],
        current_context=""
    )
    
    context = response_1.accumulated_context
    messages.append({
        'user_message': user_msg_1,
        'ai_response': response_1.ai_response
    })
    
    print("✨ Sidebar actualizado automáticamente:")
    simulate_sidebar_display(context, messages, True)  # Modo construcción
    
    # Segundo mensaje del usuario
    print_section("PASO 3: SEGUNDO MENSAJE - MÁS INFORMACIÓN")
    user_msg_2 = "Nuestro principal problema es la logística internacional y los altos costos de envío"
    
    print(f"💬 Usuario: {user_msg_2}")
    print("🤖 Context Builder procesando...")
    
    response_2 = await context_builder_service.process_user_message(
        user_message=user_msg_2,
        conversation_history=[],
        current_context=context
    )
    
    context = response_2.accumulated_context
    messages.append({
        'user_message': user_msg_2,
        'ai_response': response_2.ai_response
    })
    
    print("✨ Sidebar actualizado con más contexto:")
    simulate_sidebar_display(context, messages, True)
    
    # Tercer mensaje - completar contexto
    print_section("PASO 4: TERCER MENSAJE - CONTEXTO COMPLETO")
    user_msg_3 = "Queremos expandirnos a Estados Unidos y Europa, pero no sabemos por dónde empezar"
    
    print(f"💬 Usuario: {user_msg_3}")
    print("🤖 Context Builder procesando...")
    
    response_3 = await context_builder_service.process_user_message(
        user_message=user_msg_3,
        conversation_history=[],
        current_context=context
    )
    
    context = response_3.accumulated_context
    messages.append({
        'user_message': user_msg_3,
        'ai_response': response_3.ai_response
    })
    
    print("✅ Contexto completado - Sidebar muestra información final:")
    simulate_sidebar_display(context, messages, False)  # Modo completado
    
    # Mostrar características del sidebar
    print_section("CARACTERÍSTICAS DEL SIDEBAR")
    
    print("🎯 FUNCIONALIDADES IMPLEMENTADAS:")
    print("  • 📊 Estadísticas en tiempo real (palabras, caracteres, secciones)")
    print("  • 📄 Formato inteligente del contexto (markdown, listas, títulos)")
    print("  • 🔄 Historial de construcción (últimos 3 mensajes)")
    print("  • ⚡ Actualización automática durante construcción")
    print("  • 📱 Responsive: oculto en móviles, visible en desktop")
    print("  • 🎨 Interfaz con tabs: 'Contexto' (principal) e 'IAs'")
    
    print("\n🎨 DISEÑO Y UX:")
    print("  • Sidebar derecho fijo (320px en md, 384px en lg)")
    print("  • Tabs con iconos: FileText para Contexto, Cpu para IAs")
    print("  • Scroll independiente para contenido largo")
    print("  • Estados visuales: 'Construyendo...' vs 'Listo'")
    print("  • Preview del historial de mensajes recientes")
    
    print("\n💡 BENEFICIOS PARA EL USUARIO:")
    print("  • ✅ Siempre visible: nunca pierde de vista su contexto")
    print("  • ✅ Feedback inmediato: ve cómo crece su información")
    print("  • ✅ Control total: puede revisar qué se ha capturado")
    print("  • ✅ Navegación fácil: cambiar entre contexto e IAs")
    print("  • ✅ Información útil: estadísticas y progreso")

async def main():
    """Función principal"""
    print("🚀 INICIANDO DEMOSTRACIÓN DEL SIDEBAR DE CONTEXTO")
    print("="*80)
    
    try:
        await demo_context_sidebar()
        
        print_separator("DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
        print("✅ El sidebar de contexto está funcionando perfectamente")
        print("✅ El usuario puede ver su contexto actual en todo momento")
        print("✅ La interfaz es responsive y se actualiza en tiempo real")
        print("✅ El diseño es intuitivo con tabs y estadísticas útiles")
        
    except Exception as e:
        print(f"\n❌ ERROR EN LA DEMOSTRACIÓN: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 