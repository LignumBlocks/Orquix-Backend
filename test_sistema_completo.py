#!/usr/bin/env python3
"""
Prueba integral del sistema Orquix Backend MVP
Prueba el flujo completo: Usuario → AI Orchestrator → AI Moderator → Base de Datos
"""

import asyncio
import uuid
from datetime import datetime
from typing import List

# Imports del sistema
from app.core.database import get_async_session
from app.models import User, Project, InteractionEvent, IAResponse, ModeratedSynthesis
from app.services.ai_orchestrator import AIOrchestrator
from app.services.ai_moderator import AIModerator
from app.schemas.query import QueryRequest
from app.schemas.ai_response import StandardAIResponse, AIRequest

async def create_test_data():
    """Crear datos de prueba básicos"""
    print("📝 Creando datos de prueba...")
    
    async for session in get_async_session():
        from sqlalchemy import select
        
        # Generar email único con timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        email = f"test_sistema_{timestamp}@orquix.com"
        
        # Verificar si ya existe un usuario de prueba reciente
        existing_user_stmt = select(User).where(
            User.email.like("test_sistema_%@orquix.com")
        ).order_by(User.created_at.desc()).limit(1)
        
        result = await session.execute(existing_user_stmt)
        existing_user = result.scalar_one_or_none()
        
        # Si hay un usuario de prueba reciente (menos de 1 hora), reutilizarlo
        if (existing_user and 
            existing_user.created_at and
            (datetime.utcnow() - existing_user.created_at).total_seconds() < 3600):
            
            user = existing_user
            print(f"♻️ Reutilizando usuario existente: {user.email}")
            
            # Buscar proyecto existente de este usuario
            project_stmt = select(Project).where(
                Project.user_id == user.id,
                Project.name.like("Proyecto de Prueba Sistema%")
            ).limit(1)
            
            project_result = await session.execute(project_stmt)
            project = project_result.scalar_one_or_none()
            
            if project:
                print(f"♻️ Reutilizando proyecto existente: {project.name}")
                return user, project
        
        # Crear nuevo usuario si no existe uno reciente
        user = User(
            id=uuid.uuid4(),
            email=email,
            name=f"Usuario de Prueba Sistema {timestamp}",
            google_id=f"test_sistema_completo_{timestamp}",
            avatar_url="https://via.placeholder.com/150"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Crear proyecto de prueba
        project = Project(
            id=uuid.uuid4(),
            user_id=user.id,
            name=f"Proyecto de Prueba Sistema {timestamp}",
            description="Proyecto para probar el sistema completo",
            moderator_personality="Analytical",
            moderator_temperature=0.7,
            moderator_length_penalty=0.5
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        
        print(f"✅ Usuario creado: {user.email}")
        print(f"✅ Proyecto creado: {project.name}")
        
        return user, project

async def test_ai_orchestrator(request: AIRequest) -> List[StandardAIResponse]:
    """Probar el AI Orchestrator"""
    print("\n🤖 Probando AI Orchestrator...")
    
    from app.services.ai_orchestrator import AIOrchestrationStrategy
    
    orchestrator = AIOrchestrator()
    responses = await orchestrator.orchestrate(
        request, 
        strategy=AIOrchestrationStrategy.PARALLEL
    )
    
    print(f"✅ AI Orchestrator procesó la consulta")
    print(f"📊 Respuestas recibidas: {len(responses)}")
    
    for i, response in enumerate(responses, 1):
        print(f"  {i}. {response.ia_provider_name}: {len(response.response_text or '')} caracteres")
        if response.error_message:
            print(f"     ⚠️ Error: {response.error_message}")
    
    return responses

async def test_ai_moderator(request: AIRequest, responses: List[StandardAIResponse]) -> str:
    """Probar el AI Moderator"""
    print("\n🧠 Probando AI Moderator...")
    
    moderator = AIModerator()
    moderator_response = await moderator.synthesize_responses(responses)
    
    print(f"✅ AI Moderator generó síntesis")
    print(f"📝 Síntesis: {len(moderator_response.synthesis_text)} caracteres")
    print(f"📄 Contenido: {moderator_response.synthesis_text[:200]}...")
    print(f"🏆 Calidad: {moderator_response.quality}")
    print(f"🎯 Temas clave: {len(moderator_response.key_themes)}")
    print(f"⚠️ Contradicciones: {len(moderator_response.contradictions)}")
    
    return moderator_response.synthesis_text

async def test_database_storage(user: User, project: Project, request: AIRequest, 
                               responses: List[StandardAIResponse], synthesis: str):
    """Probar almacenamiento en base de datos"""
    print("\n💾 Probando almacenamiento en base de datos...")
    
    async for session in get_async_session():
        # Crear síntesis moderada
        moderated_synthesis = ModeratedSynthesis(
            id=uuid.uuid4(),
            synthesis_text=synthesis
        )
        session.add(moderated_synthesis)
        await session.commit()
        await session.refresh(moderated_synthesis)
        
        # Crear evento de interacción
        interaction_event = InteractionEvent(
            id=uuid.uuid4(),
            project_id=project.id,
            user_id=user.id,
            user_prompt_text=request.prompt,
            context_used_summary="Prueba de sistema completo",
            moderated_synthesis_id=moderated_synthesis.id,
            user_feedback_score=None,
            user_feedback_comment=None,
            created_at=datetime.utcnow()
        )
        session.add(interaction_event)
        await session.commit()
        await session.refresh(interaction_event)
        
        # Crear respuestas IA
        for response in responses:
            ia_response = IAResponse(
                id=uuid.uuid4(),
                interaction_event_id=interaction_event.id,
                ia_provider_name=response.ia_provider_name.value,
                raw_response_text=response.response_text or "",
                latency_ms=response.latency_ms,
                error_message=response.error_message,
                received_at=datetime.utcnow()
            )
            session.add(ia_response)
        
        await session.commit()
        
        print(f"✅ Síntesis almacenada: ID {moderated_synthesis.id}")
        print(f"✅ Evento de interacción: ID {interaction_event.id}")
        print(f"✅ Respuestas IA almacenadas: {len(responses)} registros")
        
        return interaction_event

async def test_database_retrieval(interaction_event_id: uuid.UUID):
    """Probar recuperación de datos"""
    print("\n🔍 Probando recuperación de datos...")
    
    async for session in get_async_session():
        # Recuperar evento con relaciones
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        stmt = select(InteractionEvent).options(
            selectinload(InteractionEvent.ia_responses),
            selectinload(InteractionEvent.moderated_synthesis),
            selectinload(InteractionEvent.user),
            selectinload(InteractionEvent.project)
        ).where(InteractionEvent.id == interaction_event_id)
        
        result = await session.execute(stmt)
        event = result.scalar_one_or_none()
        
        if event:
            print(f"✅ Evento recuperado: {event.user_prompt_text[:50]}...")
            print(f"✅ Usuario: {event.user.name}")
            print(f"✅ Proyecto: {event.project.name}")
            print(f"✅ Síntesis: {len(event.moderated_synthesis.synthesis_text)} caracteres")
            print(f"✅ Respuestas IA: {len(event.ia_responses)} registros")
            
            for ia_resp in event.ia_responses:
                print(f"  - {ia_resp.ia_provider_name}: {ia_resp.latency_ms}ms")
        else:
            print("❌ No se pudo recuperar el evento")
        
        return event

async def test_sistema_completo():
    """Prueba integral completa del sistema"""
    print("🚀 INICIANDO PRUEBA INTEGRAL DEL SISTEMA ORQUIX")
    print("=" * 60)
    
    try:
        # 1. Crear datos de prueba
        user, project = await create_test_data()
        
        # 2. Crear consulta de prueba
        print(f"\n❓ Consulta de prueba:")
        query = "¿Cuáles son las mejores prácticas para implementar RAG con embeddings vectoriales?"
        print(f"   '{query}'")
        
        request = AIRequest(
            prompt=query,
            max_tokens=500,
            temperature=0.7,
            project_id=str(project.id),
            user_id=str(user.id)
        )
        
        # 3. Probar AI Orchestrator
        responses = await test_ai_orchestrator(request)
        
        if not responses:
            print("❌ No se recibieron respuestas del AI Orchestrator")
            return
        
        # 4. Probar AI Moderator
        synthesis = await test_ai_moderator(request, responses)
        
        # 5. Probar almacenamiento
        interaction_event = await test_database_storage(user, project, request, responses, synthesis)
        
        # 6. Probar recuperación
        await test_database_retrieval(interaction_event.id)
        
        print("\n" + "=" * 60)
        print("🎉 ¡PRUEBA INTEGRAL COMPLETADA EXITOSAMENTE!")
        print("✅ AI Orchestrator: FUNCIONANDO")
        print("✅ AI Moderator: FUNCIONANDO") 
        print("✅ Base de Datos: FUNCIONANDO")
        print("✅ Flujo completo: EXITOSO")
        
    except Exception as e:
        print(f"\n❌ ERROR EN LA PRUEBA INTEGRAL:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sistema_completo()) 