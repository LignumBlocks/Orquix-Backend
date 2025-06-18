import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.auth import SessionUser
from app.crud import context_session as context_crud
from app.models.context_session import (
    ContextChatRequest,
    ContextChatResponse,
    ContextFinalizeRequest,
    ContextMessage,
    ContextSession,
    ContextSessionSummary
)
from app.services.context_builder import context_builder_service

logger = logging.getLogger(__name__)

router = APIRouter()

def require_auth(current_user: Optional[SessionUser] = Depends(get_current_user)) -> SessionUser:
    """Require authentication for protected endpoints."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return current_user


@router.post(
    "/projects/{project_id}/context-chat",
    response_model=ContextChatResponse,
    summary="Chat para construcción de contexto",
    description="Endpoint para chatear y construir contexto antes de enviar a las IAs principales"
)
async def context_chat(
    project_id: UUID,
    request: ContextChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """
    Procesa un mensaje del usuario en la construcción de contexto.
    
    - Si no hay session_id, crea una nueva sesión
    - Si hay session_id, continúa la conversación existente
    - Usa GPT-3.5 para generar respuestas conversacionales
    """
    try:
        user_id = UUID(current_user.id)  # Convertir string a UUID
        logger.info(f"💬 Context chat - Proyecto: {project_id}, Usuario: {user_id}")
        logger.info(f"💬 Tipos - project_id: {type(project_id)}, user_id: {type(user_id)}")
        
        # Obtener o crear sesión
        if request.session_id:
            # Continuar sesión existente
            # Convertir explícitamente a UUID si viene como string
            session_uuid = request.session_id
            if isinstance(session_uuid, str):
                session_uuid = UUID(session_uuid)
            
            logger.info(f"🔍 Buscando sesión existente: {session_uuid} (tipo: {type(session_uuid)})")
            db_session = await context_crud.get_context_session(db, session_uuid)
            logger.info(f"📋 Sesión encontrada: {db_session is not None}")
            if db_session:
                logger.info(f"📋 Sesión details: project_id={db_session.project_id}, user_id={db_session.user_id}, status={db_session.session_status}")
                logger.info(f"📋 Comparación project_id: {db_session.project_id} == {project_id} -> {db_session.project_id == project_id}")
                logger.info(f"📋 Comparación user_id: {db_session.user_id} == {user_id} -> {db_session.user_id == user_id}")
            if not db_session or db_session.project_id != project_id or db_session.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sesión de contexto no encontrada"
                )
        else:
            # Crear nueva sesión
            db_session = await context_crud.create_context_session(
                db=db,
                project_id=project_id,
                user_id=user_id,
                initial_message=request.user_message
            )
        
        # Convertir a modelo Pydantic para trabajar con el servicio
        session = context_crud.convert_interaction_to_context_session(db_session)
        
        # Procesar mensaje con GPT-3.5
        response = await context_builder_service.process_user_message(
            user_message=request.user_message,
            conversation_history=session.conversation_history,
            current_context=session.accumulated_context
        )
        
        # Actualizar session_id con el real
        response.session_id = db_session.id
        
        # Crear mensajes para actualizar la sesión
        user_message = ContextMessage(
            role="user",
            content=request.user_message,
            timestamp=datetime.utcnow(),
            message_type="information" if response.message_type == "information" else "question"
        )
        
        ai_message = ContextMessage(
            role="assistant",
            content=response.ai_response,
            timestamp=datetime.utcnow(),
            message_type=response.message_type
        )
        
        # Actualizar sesión con mensaje del usuario
        await context_crud.update_context_session(
            db=db,
            session=db_session,
            new_message=user_message,
            updated_context=response.accumulated_context
        )
        
        # Actualizar sesión con respuesta de la IA
        await context_crud.update_context_session(
            db=db,
            session=db_session,
            new_message=ai_message,
            updated_context=response.accumulated_context
        )
        
        logger.info(f"✅ Context chat procesado - Sesión: {response.session_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error en context chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando mensaje: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/context-sessions",
    response_model=List[ContextSessionSummary],
    summary="Listar sesiones de contexto",
    description="Obtiene las sesiones de construcción de contexto de un proyecto"
)
async def get_context_sessions(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """
    Obtiene las sesiones de contexto de un proyecto.
    """
    try:
        user_id = UUID(current_user.id)  # Convertir string a UUID
        sessions = await context_crud.get_project_context_sessions(
            db=db,
            project_id=project_id,
            user_id=user_id
        )
        return sessions
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo sesiones de contexto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo sesiones: {str(e)}"
        )


@router.get(
    "/context-sessions/{session_id}",
    response_model=ContextSession,
    summary="Obtener sesión de contexto",
    description="Obtiene una sesión de contexto específica con todo su historial"
)
async def get_context_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """
    Obtiene una sesión de contexto específica.
    """
    try:
        user_id = UUID(current_user.id)  # Convertir string a UUID
        db_session = await context_crud.get_context_session(db, session_id)
        if not db_session or db_session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión de contexto no encontrada"
            )
        
        # Convertir a modelo Pydantic para acceder a los campos correctamente
        session_model = context_crud.convert_interaction_to_context_session(db_session)
        return session_model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo sesión de contexto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo sesión: {str(e)}"
        )


@router.post(
    "/context-sessions/{session_id}/finalize",
    summary="Finalizar construcción de contexto",
    description="Finaliza la construcción de contexto y envía la consulta a las IAs principales"
)
async def finalize_context_session(
    session_id: UUID,
    request: ContextFinalizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """
    Finaliza la construcción de contexto y envía la consulta a las IAs principales.
    
    Este endpoint:
    1. Marca la sesión como finalizada
    2. Toma el contexto acumulado + pregunta final
    3. Lo envía al flujo normal de IAs principales
    """
    try:
        user_id = UUID(current_user.id)  # Convertir string a UUID
        logger.info(f"🏁 Finalizando sesión de contexto: {session_id}")
        
        # Obtener y validar sesión
        db_session = await context_crud.get_context_session(db, session_id)
        if not db_session or db_session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión de contexto no encontrada"
            )
        
        if db_session.session_status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La sesión ya está finalizada"
            )
        
        # Finalizar sesión
        await context_crud.finalize_context_session(db, session_id)
        
        # TODO: Aquí se integraría con el flujo normal de IAs principales
        # Por ahora retornamos información de la finalización
        
        return {
            "message": "Sesión de contexto finalizada exitosamente",
            "session_id": session_id,
            "accumulated_context": db_session.context_used_summary,
            "final_question": request.final_question,
            "ready_for_ai_processing": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error finalizando sesión de contexto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finalizando sesión: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/active-context-session",
    response_model=ContextSession,
    summary="Obtener sesión activa",
    description="Obtiene la sesión de contexto activa para un proyecto"
)
async def get_active_context_session(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SessionUser = Depends(require_auth)
):
    """
    Obtiene la sesión de contexto activa para un proyecto.
    """
    try:
        user_id = UUID(current_user.id)  # Convertir string a UUID
        db_session = await context_crud.get_active_session_for_project(
            db=db,
            project_id=project_id,
            user_id=user_id
        )
        
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay sesión de contexto activa"
            )
        
        session = context_crud.convert_interaction_to_context_session(db_session)
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo sesión activa: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo sesión activa: {str(e)}"
        )


@router.post("/context-sessions/{session_id}/generate-ai-prompts")
async def generate_ai_prompts(
    session_id: UUID,
    request: ContextFinalizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Genera los prompts reales usando el query_service y prompt_templates.
    Muestra exactamente los prompts que se enviarían a cada IA.
    """
    logger.info(f"🎯 Generando prompts usando query_service - Sesión: {session_id}")
    
    try:
        # Verificar que la sesión existe y pertenece al usuario
        session = await context_crud.get_context_session(db, session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Sesión de contexto no encontrada"
            )
        
        user_id = UUID(current_user.id)  # Convertir string a UUID
        if session.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para acceder a esta sesión"
            )
        
        # Convertir a modelo Pydantic para acceder a los campos correctamente
        session_model = context_crud.convert_interaction_to_context_session(session)
        
        # Importar los servicios correctos
        from app.services.query_service import QueryService
        from app.services.prompt_templates import PromptTemplateManager
        from app.schemas.ai_response import AIProviderEnum
        from app.schemas.query import QueryRequest, QueryType
        from app.core.config import settings
        
        # Crear instancias de los servicios
        query_service = QueryService()
        prompt_manager = PromptTemplateManager()
        
        # Determinar proveedores disponibles
        available_providers = []
        if settings.OPENAI_API_KEY:
            available_providers.append(AIProviderEnum.OPENAI)
        if settings.ANTHROPIC_API_KEY:
            available_providers.append(AIProviderEnum.ANTHROPIC)
        
        if not available_providers:
            raise HTTPException(
                status_code=500,
                detail="No hay proveedores de IA configurados"
            )
        
        # Crear una QueryRequest simulada para obtener los prompts
        query_request = QueryRequest(
            user_question=request.final_question,
            query_type=QueryType.CONTEXT_AWARE,
            user_id=user_id,
            project_id=session.project_id,
            max_tokens=1200,
            temperature=0.7
        )
        
        # Usar el contexto acumulado de la sesión
        context_text = session_model.accumulated_context or ""
        
        # Generar prompts para cada proveedor usando el sistema oficial
        ai_prompts = {}
        
        for provider in available_providers:
            try:
                # Usar el método oficial del query_service para construir prompts
                prompt_data = prompt_manager.build_prompt_for_provider(
                    provider=provider,
                    user_question=query_request.user_question,
                    context_text=context_text,
                    additional_vars={
                        'timestamp': datetime.utcnow().isoformat(),
                        'project_name': f"Proyecto-{str(session.project_id)[:8]}"
                    }
                )
                
                # Optimizar el prompt para el proveedor
                optimized_prompt = prompt_manager.optimize_prompt_for_provider(
                    provider, prompt_data, query_request.max_tokens
                )
                
                # Obtener modelo específico del proveedor
                if provider == AIProviderEnum.OPENAI:
                    model = "gpt-4o-mini"
                elif provider == AIProviderEnum.ANTHROPIC:
                    model = "claude-3-haiku-20240307"
                else:
                    model = "unknown"
                
                ai_prompts[provider.value.lower()] = {
                    "provider": f"{provider.value.title()}",
                    "model": model,
                    "system_message": optimized_prompt['system_message'],
                    "user_prompt": optimized_prompt['user_message'],
                    "parameters": {
                        "max_tokens": query_request.max_tokens,
                        "temperature": query_request.temperature
                    },
                    "template_used": "prompt_templates_v2.0"
                }
                
            except Exception as e:
                logger.error(f"Error generando prompt para {provider}: {e}")
                ai_prompts[provider.value.lower()] = {
                    "provider": f"{provider.value.title()}",
                    "error": f"Error generando prompt: {str(e)}"
                }
        
        logger.info(f"✅ Prompts generados usando query_service para {len(ai_prompts)} proveedores")
        
        return {
            "session_id": session_id,
            "ai_prompts": ai_prompts,
            "prompt_system": "query_service + prompt_templates",
            "context_used": context_text[:200] + "..." if len(context_text) > 200 else context_text,
            "final_question": request.final_question
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando prompts con query_service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando prompts: {str(e)}"
        )


@router.post("/context-sessions/{session_id}/query-ais")
async def query_ais_individually(
    session_id: UUID,
    request: ContextFinalizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Endpoint específico para enviar los prompts a las IAs y obtener respuestas individuales.
    Se ejecuta después de generar los prompts.
    """
    logger.info(f"🤖 Consultando IAs individualmente - Sesión: {session_id}")
    
    try:
        # Verificar que la sesión existe y pertenece al usuario
        session = await context_crud.get_context_session(db, session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Sesión de contexto no encontrada"
            )
        
        user_id = UUID(current_user.id)
        if session.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para acceder a esta sesión"
            )
        
        # Convertir a modelo Pydantic
        session_model = context_crud.convert_interaction_to_context_session(session)
        
        # Importar servicios necesarios
        from app.services.ai_orchestrator import AIOrchestrator
        from app.schemas.ai_response import AIRequest, AIProviderEnum
        from app.core.config import settings
        import time
        
        # Crear instancia del orquestador
        orchestrator = AIOrchestrator()
        
        # Usar el contexto acumulado de la sesión
        context_text = session_model.accumulated_context or ""
        
        # Crear AIRequest para el orquestador
        # Combinar contexto y pregunta en el prompt
        full_prompt = f"""Contexto:
{context_text}

Pregunta del usuario:
{request.final_question}

Por favor, proporciona una respuesta detallada basada en el contexto proporcionado."""

        ai_request = AIRequest(
            prompt=full_prompt,
            max_tokens=1200,
            temperature=0.7,
            user_id=str(user_id),
            project_id=str(session.project_id)
        )
        
        # Ejecutar consultas individuales a las IAs
        start_time = time.time()
        individual_responses = []
        
        # Obtener proveedores disponibles
        available_providers = orchestrator.get_available_providers()
        
        try:
            # Consultar cada proveedor individualmente
            for provider in available_providers:
                logger.info(f"🤖 Consultando {provider.value.title()}...")
                provider_start = time.time()
                
                try:
                    ai_response = await orchestrator.generate_single_response(
                        request=ai_request,
                        provider=provider
                    )
                    provider_time = time.time() - provider_start
                    
                    # Determinar modelo según el proveedor
                    model = "gpt-4o-mini" if provider == AIProviderEnum.OPENAI else "claude-3-haiku-20240307"
                    
                    if ai_response.status.value == "success":
                        individual_responses.append({
                            "provider": provider.value.lower(),
                            "model": model,
                            "content": ai_response.response_text,
                            "processing_time_ms": int(provider_time * 1000),
                            "success": True,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        logger.info(f"✅ {provider.value.title()} respondió en {provider_time:.2f}s")
                    else:
                        individual_responses.append({
                            "provider": provider.value.lower(),
                            "model": model,
                            "error": ai_response.error_message or "Error desconocido",
                            "processing_time_ms": int(provider_time * 1000),
                            "success": False,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        logger.error(f"❌ Error en {provider.value.title()}: {ai_response.error_message}")
                    
                except Exception as e:
                    provider_time = time.time() - provider_start
                    logger.error(f"❌ Error en {provider.value.title()}: {e}")
                    individual_responses.append({
                        "provider": provider.value.lower(),
                        "model": "gpt-4o-mini" if provider == AIProviderEnum.OPENAI else "claude-3-haiku-20240307",
                        "error": str(e),
                        "processing_time_ms": int(provider_time * 1000),
                        "success": False,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
        except Exception as e:
            logger.error(f"❌ Error general consultando IAs: {e}")
        
        total_time = time.time() - start_time
        successful_responses = [r for r in individual_responses if r.get("success", False)]
        
        logger.info(f"✅ Consulta individual completada - {len(successful_responses)}/{len(individual_responses)} exitosas en {total_time:.2f}s")
        
        return {
            "session_id": session_id,
            "user_question": request.final_question,
            "individual_responses": individual_responses,
            "total_processing_time_ms": int(total_time * 1000),
            "successful_responses": len(successful_responses),
            "total_responses": len(individual_responses),
            "context_used": context_text[:200] + "..." if len(context_text) > 200 else context_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error consultando IAs individualmente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando IAs: {str(e)}"
        )


@router.post("/context-sessions/{session_id}/retry-ai/{provider}")
async def retry_single_ai(
    session_id: UUID,
    provider: str,
    request: ContextFinalizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reintenta consultar una IA específica que falló anteriormente.
    """
    logger.info(f"🔄 Reintentando {provider.upper()} - Sesión: {session_id}")
    
    try:
        # Verificar que la sesión existe y pertenece al usuario
        session = await context_crud.get_context_session(db, session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Sesión de contexto no encontrada"
            )

        user_id = current_user.get("user_id")
        if session.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes acceso a esta sesión"
            )

        # Obtener el modelo de sesión para el contexto
        session_model = await context_crud.get_context_session_model(db, session_id)
        if not session_model:
            raise HTTPException(
                status_code=404,
                detail="Modelo de sesión no encontrado"
            )

        # Importar servicios necesarios
        from app.services.ai_orchestrator import AIOrchestrator
        from app.schemas.ai_response import AIRequest
        import time

        # Crear instancia del orquestrador
        orchestrator = AIOrchestrator()
        
        # Usar el contexto acumulado de la sesión
        context_text = session_model.accumulated_context or ""
        
        # Crear prompt completo
        full_prompt = f"""Contexto:
{context_text}

Pregunta del usuario:
{request.final_question}

Por favor, proporciona una respuesta detallada basada en el contexto proporcionado."""

        ai_request = AIRequest(
            prompt=full_prompt,
            max_tokens=1200,
            temperature=0.7,
            user_id=str(user_id),
            project_id=str(session.project_id)
        )

        # Mapear el proveedor string a enum
        from app.services.ai_adapters.base import AIProviderEnum
        provider_map = {
            "openai": AIProviderEnum.OPENAI,
            "anthropic": AIProviderEnum.ANTHROPIC
        }
        
        if provider.lower() not in provider_map:
            raise HTTPException(
                status_code=400,
                detail=f"Proveedor no válido: {provider}. Debe ser 'openai' o 'anthropic'"
            )

        provider_enum = provider_map[provider.lower()]
        
        # Ejecutar consulta individual
        start_time = time.time()
        logger.info(f"🤖 Reintentando {provider.upper()}...")
        
        ai_response = await orchestrator.generate_single_response(ai_request, provider_enum)
        provider_time = time.time() - start_time
        
        # Procesar respuesta
        if ai_response.status.value == "success":
            response_data = {
                "provider": provider.lower(),
                "model": ai_response.model,
                "content": ai_response.response_text,
                "processing_time_ms": int(provider_time * 1000),
                "success": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.info(f"✅ {provider.upper()} respondió correctamente en {provider_time:.2f}s")
        else:
            response_data = {
                "provider": provider.lower(),
                "model": ai_response.model or "unknown",
                "error": ai_response.error_message or "Error desconocido",
                "processing_time_ms": int(provider_time * 1000),
                "success": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.error(f"❌ {provider.upper()} falló nuevamente: {ai_response.error_message}")

        total_time = time.time() - start_time
        
        return {
            "session_id": str(session_id),
            "provider": provider.lower(),
            "response": response_data,
            "total_processing_time_ms": int(total_time * 1000),
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error reintentando {provider}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno reintentando {provider}: {str(e)}"
        ) 