import pytest
from uuid import UUID, uuid4
from datetime import datetime, timezone
from app.services.pre_analyst import pre_analyst_service
from app.services.clarification_manager import clarification_manager
from app.services.prompt_templates import PromptTemplateManager
from app.schemas.ai_response import AIProviderEnum
from app.models.pre_analysis import (
    PreAnalysisResult,
    ClarificationRequest,
    ClarificationResponse
)

# Datos de ejemplo para las pruebas
CONTEXT_EXAMPLE = """Durante la última década, la penetración de soluciones de IA conversacional y automatización de procesos robóticos (RPA) en los call-centers latinoamericanos ha ido en aumento, impulsada por la rápida expansión del e-commerce regional y la creciente demanda de atención multilingüe 24/7. Diversos estudios—entre ellos el informe "The Service Automation Index" del MIT (2024) y el reporte de la OECD "Automation and Emerging Markets" (2023)—coinciden en que el sector servicios será uno de los más transformados antes de 2030. Mientras los análisis optimistas destacan mejoras en productividad, creación de nuevos roles especializados y oportunidades de upskilling, las proyecciones pesimistas advierten de una posible sustitución del 20 % a 40 % de los agentes humanos, con riesgos de precarización laboral y profundización de la desigualdad salarial en la región."""

# Simulamos una interacción previa para tener contexto acumulado
PREVIOUS_INTERACTION = {
    'timestamp': '2024-03-20T15:30:00Z',
    'user_prompt': '¿Qué son los call centers?',
    'refined_prompt': 'Explica qué son los call centers, su función principal y su importancia en el servicio al cliente moderno.',
    'synthesis': """Los call centers son centros de atención telefónica que funcionan como punto de contacto entre empresas y clientes. Sus funciones principales incluyen:
1. Atención al cliente y soporte técnico
2. Ventas y telemarketing
3. Gestión de reclamos y consultas
4. Servicios post-venta

En el contexto actual, los call centers han evolucionado para incluir múltiples canales de comunicación (omnicanalidad) y tecnologías avanzadas como IA y automatización."""
}

VAGUE_QUERY = "¿qué opinas sobre la automatización en call centers?"

@pytest.mark.asyncio
async def test_force_proceed_flow():
    """
    Prueba el flujo completo de force_proceed con contexto acumulado:
    1. PreAnalyst analiza una pregunta vaga sobre automatización
    2. Sugiere clarificaciones pero genera refined_prompt usando el contexto
    3. Usuario fuerza avance sin responder preguntas
    4. Sistema usa el refined_prompt con TODO el contexto para las IAs
    """
    print("\n=== Test de Force Proceed con Clarificaciones Opt-in y Contexto Acumulado ===")
    
    # Setup
    project_id = uuid4()
    user_id = uuid4()
    prompt_manager = PromptTemplateManager()
    
    print("\n📝 Historial de Interacción:")
    print(f"Pregunta anterior: {PREVIOUS_INTERACTION['user_prompt']}")
    print(f"Síntesis previa: {PREVIOUS_INTERACTION['synthesis'][:200]}...")
    
    print("\n❓ Nueva pregunta del usuario:", VAGUE_QUERY)
    print("\n📚 Contexto del proyecto:", CONTEXT_EXAMPLE[:100] + "...")
    
    # Paso 1: Análisis inicial con PreAnalyst
    print("\n1️⃣ Análisis PreAnalyst")
    analysis_result = await pre_analyst_service.analyze_prompt(VAGUE_QUERY)
    
    # Verificar que tenemos preguntas de clarificación Y refined_prompt
    assert len(analysis_result.clarification_questions) > 0, "Debería sugerir clarificaciones para pregunta vaga"
    assert analysis_result.refined_prompt_candidate is not None, "Debería generar refined_prompt"
    
    print(f"🔍 Intención interpretada: {analysis_result.interpreted_intent}")
    print("\n❓ Preguntas sugeridas:")
    for q in analysis_result.clarification_questions:
        print(f"   • {q}")
    print(f"\n📝 Prompt refinado: {analysis_result.refined_prompt_candidate}")
    
    # Paso 2: Iniciar sesión de clarificación
    print("\n2️⃣ Iniciando sesión de clarificación")
    clarification_response = await clarification_manager.start_clarification_session(
        project_id=project_id,
        user_id=user_id,
        initial_prompt=VAGUE_QUERY
    )
    
    print(f"Session ID: {clarification_response.session_id}")
    print("Estado inicial:", "Completo ✅" if clarification_response.is_complete else "Esperando clarificación ⏳")
    
    # Paso 3: Forzar avance sin responder preguntas
    print("\n3️⃣ Usuario elige 'Continuar de todos modos'")
    force_request = ClarificationRequest(
        session_id=clarification_response.session_id,
        project_id=project_id,
        user_response="",
        force_proceed=True
    )
    
    # Simular force_proceed
    forced_response = clarification_manager.force_proceed_session(force_request.session_id)
    assert forced_response is not None, "Debería obtener respuesta al forzar"
    assert forced_response.is_complete, "Sesión debería estar completa"
    assert not forced_response.next_questions, "No debería haber más preguntas"
    
    print("✅ Sesión marcada como completa")
    print("🚫 Preguntas de clarificación: omitidas")
    
    # Paso 4: Preparar prompts para cada IA usando el contexto acumulado
    print("\n4️⃣ Preparando prompts completos para IAs (con todo el contexto)")
    
    # Lista de chunks de contexto en orden de relevancia
    context_chunks = [
        # Contexto del proyecto actual
        {
            'source_type': 'project_context',
            'similarity_score': 0.95,
            'content_text': CONTEXT_EXAMPLE
        },
        # Interacción previa relevante
        {
            'source_type': 'interaction_history',
            'similarity_score': 0.85,
            'content_text': f"""[Interacción previa - {PREVIOUS_INTERACTION['timestamp']}]
Pregunta: {PREVIOUS_INTERACTION['refined_prompt']}
Síntesis: {PREVIOUS_INTERACTION['synthesis']}"""
        }
    ]
    
    # Mostrar prompts completos para cada proveedor
    for provider in [AIProviderEnum.OPENAI, AIProviderEnum.ANTHROPIC]:
        print(f"\n\n🤖 PROMPT COMPLETO PARA {provider}")
        print("=" * 80)
        
        # Formatear contexto según el template del proveedor
        context_formatted = prompt_manager.format_context_for_provider(
            provider=provider,
            context_chunks=context_chunks
        )
        
        # Construir prompt completo
        prompt_data = prompt_manager.build_prompt_for_provider(
            provider=provider,
            user_question=analysis_result.refined_prompt_candidate,
            context_text=context_formatted,
            additional_vars={
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'project_name': 'Test Project',
                'user_name': 'Test User'
            }
        )
        
        print("\n📋 SYSTEM MESSAGE:")
        print("-" * 40)
        print(prompt_data['system_message'])
        
        print("\n📚 CONTEXTO FORMATEADO:")
        print("-" * 40)
        print(context_formatted)
        
        print("\n💬 USER MESSAGE:")
        print("-" * 40)
        print(prompt_data['user_message']) 