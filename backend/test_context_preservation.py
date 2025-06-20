#!/usr/bin/env python3
"""
Test para verificar que el contexto preserve información completa
incluyendo información valiosa de preguntas
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.context_builder import ContextBuilderService

async def test_question_context_extraction():
    """Test de extracción de información de preguntas"""
    print("🧪 Test: Extracción de información de preguntas...")
    
    builder = ContextBuilderService()
    
    # Contexto inicial
    initial_context = "Startup que ofrece software de gestión para clínicas dentales, actualmente en fase beta"
    
    # Pregunta con información valiosa (como la del usuario)
    question = "¿Qué estrategia combinada de marketing digital y pricing me permite alcanzar 50 clientes de pago en México y Colombia, manteniendo un CAC ≤ 150 USD con un presupuesto de 2,000 USD al mes?"
    
    print(f"\n📝 Contexto inicial: {initial_context}")
    print(f"❓ Pregunta del usuario: {question}")
    
    try:
        result = await builder.process_user_message(
            user_message=question,
            conversation_history=[],  # Lista vacía para el historial
            current_context=initial_context
        )
        
        print(f"\n✅ Respuesta GPT:")
        print(f"   Tipo: {result.message_type}")
        print(f"   Respuesta: {result.ai_response[:100]}...")
        print(f"   Contexto Final: {result.accumulated_context}")
        
        # Verificar que la pregunta extrajo información valiosa
        final_context = result.accumulated_context
        
        # Información que debería extraerse de la pregunta
        expected_info = {
            '50 clientes': '50' in final_context,
            'México y Colombia': ('méxico' in final_context.lower() and 'colombia' in final_context.lower()),
            'CAC 150 USD': '150' in final_context,
            'presupuesto 2000': '2000' in final_context or '2,000' in final_context,
            'marketing digital': 'marketing' in final_context.lower()
        }
        
        print(f"\n🔍 Verificaciones de extracción:")
        all_passed = True
        for info, found in expected_info.items():
            status = "✅" if found else "❌"
            print(f"   {status} {info}: {found}")
            if not found:
                all_passed = False
        
        # Verificar que el contexto final tenga más información
        initial_words = len(initial_context.split())
        final_words = len(final_context.split())
        
        print(f"\n📊 Palabras contexto inicial: {initial_words}")
        print(f"📊 Palabras contexto final: {final_words}")
        context_grew = final_words > initial_words
        print(f"📈 Contexto creció: {'✅' if context_grew else '❌'}")
        
        success = all_passed and context_grew
        
        if success:
            print(f"\n🎉 ¡ÉXITO! La pregunta agregó información valiosa al contexto")
        else:
            print(f"\n❌ FALLO: La pregunta no agregó suficiente información al contexto")
            
        return success
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_information_vs_question_context():
    """Test comparando extracción de información vs preguntas"""
    print("\n🧪 Test: Comparación información vs pregunta...")
    
    builder = ContextBuilderService()
    
    # Test con información directa
    info_message = "Nuestro mercado principal es México y Colombia, queremos conseguir los primeros 50 clientes"
    result_info = await builder.process_user_message(info_message, [], "")
    
    # Test con pregunta que contiene la misma información
    question_message = "¿Cómo podemos conseguir nuestros primeros 50 clientes en México y Colombia?"
    result_question = await builder.process_user_message(question_message, [], "")
    
    print(f"\n📝 Información directa: {info_message}")
    print(f"   Contexto Final: {result_info.accumulated_context}")
    print(f"   Tipo: {result_info.message_type}")
    
    print(f"\n❓ Pregunta equivalente: {question_message}")
    print(f"   Contexto Final: {result_question.accumulated_context}")
    print(f"   Tipo: {result_question.message_type}")
    
    # Ambos deberían extraer información similar
    info_context = result_info.accumulated_context
    question_context = result_question.accumulated_context
    
    info_has_50 = '50' in info_context
    question_has_50 = '50' in question_context
    
    info_has_countries = 'méxico' in info_context.lower() and 'colombia' in info_context.lower()
    question_has_countries = 'méxico' in question_context.lower() and 'colombia' in question_context.lower()
    
    print(f"\n🔍 Comparación de extracción:")
    print(f"   Información directa extrajo '50 clientes': {'✅' if info_has_50 else '❌'}")
    print(f"   Pregunta extrajo '50 clientes': {'✅' if question_has_50 else '❌'}")
    print(f"   Información directa extrajo países: {'✅' if info_has_countries else '❌'}")
    print(f"   Pregunta extrajo países: {'✅' if question_has_countries else '❌'}")
    
    success = question_has_50 and question_has_countries
    
    if success:
        print(f"\n🎉 ¡ÉXITO! Las preguntas extraen información tan bien como las declaraciones")
    else:
        print(f"\n❌ FALLO: Las preguntas no extraen suficiente información")
        
    return success

async def test_no_duplication():
    """Test para verificar que no se duplique información idéntica"""
    print("\n🧪 Test: No duplicación de información idéntica...")
    
    builder = ContextBuilderService()
    
    # Contexto inicial
    initial_context = "Startup que ofrece software de gestión para clínicas dentales, actualmente en fase beta"
    
    # Mismo mensaje dos veces (como podría pasar en la UI)
    same_message = "Tengo una startup que ofrece software de gestión para clínicas dentales. Aún estamos en fase beta"
    
    print(f"\n📝 Contexto inicial: {initial_context}")
    print(f"📝 Mensaje (primera vez): {same_message}")
    
    # Primera vez
    result1 = await builder.process_user_message(
        user_message=same_message,
        conversation_history=[],
        current_context=initial_context
    )
    
    context_after_first = result1.accumulated_context
    print(f"📝 Contexto después de primera vez: {context_after_first}")
    
    # Segunda vez - el mismo mensaje
    print(f"\n📝 Mensaje (segunda vez - duplicado): {same_message}")
    result2 = await builder.process_user_message(
        user_message=same_message,
        conversation_history=[],
        current_context=context_after_first
    )
    
    context_after_second = result2.accumulated_context
    print(f"📝 Contexto después de segunda vez: {context_after_second}")
    
    # Verificar que no haya duplicación
    words_first = context_after_first.split()
    words_second = context_after_second.split()
    
    # Contar cuántas veces aparece "startup"
    startup_count_first = context_after_first.lower().count('startup')
    startup_count_second = context_after_second.lower().count('startup')
    
    # Contar cuántas veces aparece "clínicas dentales"
    dental_count_first = context_after_first.lower().count('dental')
    dental_count_second = context_after_second.lower().count('dental')
    
    print(f"\n🔍 Verificaciones de duplicación:")
    print(f"   Palabras primera vez: {len(words_first)}")
    print(f"   Palabras segunda vez: {len(words_second)}")
    print(f"   'startup' primera vez: {startup_count_first}")
    print(f"   'startup' segunda vez: {startup_count_second}")
    print(f"   'dental' primera vez: {dental_count_first}")
    print(f"   'dental' segunda vez: {dental_count_second}")
    
    # El contexto NO debería crecer significativamente la segunda vez
    growth_ratio = len(words_second) / len(words_first) if len(words_first) > 0 else 0
    no_significant_growth = growth_ratio < 1.3  # Menos del 30% de crecimiento
    
    # No debería duplicarse la información clave
    no_startup_duplication = startup_count_second <= startup_count_first + 1
    no_dental_duplication = dental_count_second <= dental_count_first + 1
    
    success = no_significant_growth and no_startup_duplication and no_dental_duplication
    
    print(f"\n📊 Resultados:")
    print(f"   Crecimiento controlado (<30%): {'✅' if no_significant_growth else '❌'} ({growth_ratio:.2f})")
    print(f"   Sin duplicación de 'startup': {'✅' if no_startup_duplication else '❌'}")
    print(f"   Sin duplicación de 'dental': {'✅' if no_dental_duplication else '❌'}")
    
    if success:
        print(f"\n🎉 ¡ÉXITO! No hay duplicación de información")
    else:
        print(f"\n❌ FALLO: Se está duplicando información")
        
    return success

async def test_context_chat_simulation():
    """Test para simular el flujo completo del endpoint context_chat"""
    print("\n🧪 Test: Simulación completa del flujo context_chat...")
    
    builder = ContextBuilderService()
    
    # Simular el contexto que viene de la base de datos
    initial_db_context = "Startup que ofrece software de gestión para clínicas dentales, actualmente en fase beta"
    
    # Simular el enhanced_context después de _automatically_include_moderator_synthesis
    # (que debería ser igual si no hay síntesis del moderador)
    enhanced_context = initial_db_context  # Sin síntesis del moderador
    
    # Primer mensaje del usuario
    user_message1 = "Tengo una startup que ofrece software de gestión para clínicas dentales. Aún estamos en fase beta"
    
    print(f"\n📝 Contexto inicial de BD: {initial_db_context}")
    print(f"📝 Enhanced context: {enhanced_context}")
    print(f"📝 Mensaje usuario 1: {user_message1}")
    
    # Procesar primer mensaje
    response1 = await builder.process_user_message(
        user_message=user_message1,
        conversation_history=[],
        current_context=enhanced_context
    )
    
    print(f"📝 Contexto después mensaje 1: {response1.accumulated_context}")
    
    # Simular segundo mensaje (diferente información)
    user_message2 = "Estamos considerando campañas en Google Ads pero no sabemos cuánto invertir"
    
    print(f"\n📝 Mensaje usuario 2: {user_message2}")
    
    # Procesar segundo mensaje (usando el contexto del primero)
    response2 = await builder.process_user_message(
        user_message=user_message2,
        conversation_history=[],  # Historial vacío para simplificar
        current_context=response1.accumulated_context  # Usar el contexto acumulado
    )
    
    print(f"📝 Contexto después mensaje 2: {response2.accumulated_context}")
    
    # Verificar que no haya duplicación
    context_final = response2.accumulated_context
    
    # Contar occurrencias de palabras clave
    startup_count = context_final.lower().count('startup')
    dental_count = context_final.lower().count('dental')
    beta_count = context_final.lower().count('beta')
    
    print(f"\n🔍 Análisis del contexto final:")
    print(f"   Total caracteres: {len(context_final)}")
    print(f"   Occurrencias 'startup': {startup_count}")
    print(f"   Occurrencias 'dental': {dental_count}")
    print(f"   Occurrencias 'beta': {beta_count}")
    
    # Verificar que no hay duplicación excesiva
    no_startup_duplication = startup_count <= 2  # Máximo 2 veces
    no_dental_duplication = dental_count <= 2   # Máximo 2 veces  
    no_beta_duplication = beta_count <= 2       # Máximo 2 veces
    
    # Verificar que contiene información de ambos mensajes
    has_google_ads = 'google ads' in context_final.lower()
    has_investment = 'invertir' in context_final.lower() or 'inversión' in context_final.lower()
    
    # Verificar que no hay duplicación semántica excesiva
    # Buscar patrones de duplicación
    import re
    startup_software_pattern = r'startup.*software.*gestión.*clínicas.*dentales'
    beta_pattern = r'fase.*beta'
    
    startup_software_matches = len(re.findall(startup_software_pattern, context_final.lower()))
    beta_matches = len(re.findall(beta_pattern, context_final.lower()))
    
    no_semantic_duplication = startup_software_matches <= 1 and beta_matches <= 1
    
    success = (no_startup_duplication and no_dental_duplication and 
              no_beta_duplication and has_google_ads and has_investment and
              no_semantic_duplication)
    
    print(f"\n📊 Resultados:")
    print(f"   Sin duplicación excesiva de 'startup': {'✅' if no_startup_duplication else '❌'}")
    print(f"   Sin duplicación excesiva de 'dental': {'✅' if no_dental_duplication else '❌'}")
    print(f"   Sin duplicación excesiva de 'beta': {'✅' if no_beta_duplication else '❌'}")
    print(f"   Sin duplicación semántica: {'✅' if no_semantic_duplication else '❌'}")
    print(f"   Contiene info de Google Ads: {'✅' if has_google_ads else '❌'}")
    print(f"   Contiene info de inversión: {'✅' if has_investment else '❌'}")
    print(f"   Patrones 'startup+software+dental': {startup_software_matches}")
    print(f"   Patrones 'fase+beta': {beta_matches}")
    
    if success:
        print(f"\n🎉 ¡ÉXITO! Flujo completo sin duplicación")
    else:
        print(f"\n❌ FALLO: Hay duplicación en el flujo completo")
        
    return success

async def main():
    print("🚀 Iniciando tests de extracción de contexto de preguntas...")
    
    test1_passed = await test_question_context_extraction()
    test2_passed = await test_information_vs_question_context()
    test3_passed = await test_no_duplication()
    test4_passed = await test_context_chat_simulation()
    
    print(f"\n📊 RESULTADOS:")
    print(f"   Test 1 (Extracción de pregunta): {'✅ PASÓ' if test1_passed else '❌ FALLÓ'}")
    print(f"   Test 2 (Comparación info vs pregunta): {'✅ PASÓ' if test2_passed else '❌ FALLÓ'}")
    print(f"   Test 3 (No duplicación de información): {'✅ PASÓ' if test3_passed else '❌ FALLÓ'}")
    print(f"   Test 4 (Simulación completa del flujo context_chat): {'✅ PASÓ' if test4_passed else '❌ FALLÓ'}")
    
    if test1_passed and test2_passed and test3_passed and test4_passed:
        print(f"\n🎉 ¡TODOS LOS TESTS PASARON!")
        print(f"✅ Las preguntas ahora agregan información valiosa al contexto")
    else:
        print(f"\n❌ Algunos tests fallaron - revisar implementación")

if __name__ == "__main__":
    asyncio.run(main()) 