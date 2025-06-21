from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.models import IAPrompt, IAResponse


async def create_ia_prompt(
    db: AsyncSession,
    project_id: UUID,
    context_session_id: Optional[UUID],
    original_query: str,
    generated_prompt: str
) -> IAPrompt:
    """Crear un nuevo prompt de IA"""
    ia_prompt = IAPrompt(
        project_id=project_id,
        context_session_id=context_session_id,
        original_query=original_query,
        generated_prompt=generated_prompt,
        status="generated"
    )
    
    db.add(ia_prompt)
    await db.commit()
    await db.refresh(ia_prompt)
    return ia_prompt


async def create_moderator_prompt(
    db: AsyncSession,
    project_id: UUID,
    context_session_id: Optional[UUID],
    original_query: str,
    generated_prompt: str,
    responses_to_synthesize: int
) -> IAPrompt:
    """Crear un nuevo prompt del moderador para síntesis"""
    ia_prompt = IAPrompt(
        project_id=project_id,
        context_session_id=context_session_id,
        original_query=f"[MODERADOR] Síntesis de {responses_to_synthesize} respuestas: {original_query}",
        generated_prompt=generated_prompt,
        status="moderator_synthesis"
    )
    
    db.add(ia_prompt)
    await db.commit()
    await db.refresh(ia_prompt)
    return ia_prompt


async def get_ia_prompt_by_id(db: AsyncSession, prompt_id: UUID) -> Optional[IAPrompt]:
    """Obtener un prompt de IA por ID"""
    result = await db.execute(
        select(IAPrompt)
        .options(selectinload(IAPrompt.ia_responses))
        .where(IAPrompt.id == prompt_id)
        .where(IAPrompt.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_ia_prompts_by_project(
    db: AsyncSession, 
    project_id: UUID,
    limit: int = 50
) -> List[IAPrompt]:
    """Obtener prompts de IA por proyecto"""
    result = await db.execute(
        select(IAPrompt)
        .where(IAPrompt.project_id == project_id)
        .where(IAPrompt.deleted_at.is_(None))
        .order_by(IAPrompt.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_all_prompts_by_project_with_type(
    db: AsyncSession, 
    project_id: UUID,
    limit: int = 50
) -> List[Dict]:
    """Obtener todos los prompts de un proyecto clasificados por tipo"""
    result = await db.execute(
        select(IAPrompt)
        .options(selectinload(IAPrompt.ia_responses))
        .where(IAPrompt.project_id == project_id)
        .where(IAPrompt.deleted_at.is_(None))
        .order_by(IAPrompt.created_at.desc())
        .limit(limit)
    )
    
    prompts = list(result.scalars().all())
    
    # Clasificar prompts por tipo
    classified_prompts = []
    for prompt in prompts:
        prompt_type = "moderator" if prompt.status == "moderator_synthesis" else "ai_provider"
        is_moderator = prompt.original_query.startswith("[MODERADOR]") if prompt.original_query else False
        
        classified_prompts.append({
            "id": str(prompt.id),
            "type": prompt_type,
            "is_moderator": is_moderator,
            "original_query": prompt.original_query,
            "generated_prompt": prompt.generated_prompt,
            "status": prompt.status,
            "created_at": prompt.created_at,
            "responses_count": len(prompt.ia_responses) if prompt.ia_responses else 0,
            "context_session_id": str(prompt.context_session_id) if prompt.context_session_id else None
        })
    
    return classified_prompts


async def update_ia_prompt(
    db: AsyncSession,
    prompt_id: UUID,
    edited_prompt: str
) -> Optional[IAPrompt]:
    """Actualizar un prompt de IA con versión editada"""
    await db.execute(
        update(IAPrompt)
        .where(IAPrompt.id == prompt_id)
        .values(
            edited_prompt=edited_prompt,
            is_edited=True,
            status="edited"
        )
    )
    await db.commit()
    
    return await get_ia_prompt_by_id(db, prompt_id)


async def mark_prompt_as_executed(
    db: AsyncSession,
    prompt_id: UUID
) -> Optional[IAPrompt]:
    """Marcar un prompt como ejecutado"""
    await db.execute(
        update(IAPrompt)
        .where(IAPrompt.id == prompt_id)
        .values(status="executed")
    )
    await db.commit()
    
    return await get_ia_prompt_by_id(db, prompt_id)


async def create_ia_response(
    db: AsyncSession,
    ia_prompt_id: UUID,
    provider: str,
    response_text: str,
    status: str,
    latency_ms: int,
    error_message: Optional[str] = None
) -> IAResponse:
    """Crear una nueva respuesta de IA"""
    from datetime import datetime
    
    ia_response = IAResponse(
        ia_prompt_id=ia_prompt_id,
        ia_provider_name=provider,
        raw_response_text=response_text,
        latency_ms=latency_ms,
        error_message=error_message,
        received_at=datetime.utcnow()
    )
    
    db.add(ia_response)
    await db.commit()
    await db.refresh(ia_response)
    return ia_response 