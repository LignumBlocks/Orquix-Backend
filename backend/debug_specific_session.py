#!/usr/bin/env python3
"""
Script para debuggear una sesión específica.
"""

import asyncio
from uuid import UUID
from sqlmodel import select
from app.core.database import get_db
from app.models.models import InteractionEvent

async def debug_specific_session():
    """Debuggea una sesión específica."""
    
    session_id_str = "bb64f3f0-6f29-4092-9d24-1ec19588d9ed"
    project_id_str = "c9cc165a-6fed-4134-bf20-0e5897e3b7c8"
    user_id_str = "550e8400-e29b-41d4-a716-446655440000"
    
    async for db in get_db():
        print(f"🔍 DEBUGGING SESIÓN ESPECÍFICA: {session_id_str}")
        print("=" * 60)
        
        # Convertir a UUIDs
        session_uuid = UUID(session_id_str)
        project_uuid = UUID(project_id_str)
        user_uuid = UUID(user_id_str)
        
        print(f"📊 IDs convertidos:")
        print(f"  - Session UUID: {session_uuid} (tipo: {type(session_uuid)})")
        print(f"  - Project UUID: {project_uuid} (tipo: {type(project_uuid)})")
        print(f"  - User UUID: {user_uuid} (tipo: {type(user_uuid)})")
        
        # Buscar la sesión exacta
        query = select(InteractionEvent).where(
            InteractionEvent.id == session_uuid,
            InteractionEvent.interaction_type == "context_building",
            InteractionEvent.deleted_at.is_(None)
        )
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        print(f"\n🔍 RESULTADO DE BÚSQUEDA:")
        print(f"  - Sesión encontrada: {session is not None}")
        
        if session:
            print(f"  - ID encontrado: {session.id} (tipo: {type(session.id)})")
            print(f"  - Project ID: {session.project_id} (tipo: {type(session.project_id)})")
            print(f"  - User ID: {session.user_id} (tipo: {type(session.user_id)})")
            print(f"  - Estado: {session.session_status}")
            print(f"  - Tipo: {session.interaction_type}")
            
            # Comparaciones
            print(f"\n🧪 COMPARACIONES:")
            print(f"  - Project ID match: {session.project_id} == {project_uuid} -> {session.project_id == project_uuid}")
            print(f"  - User ID match: {session.user_id} == {user_uuid} -> {session.user_id == user_uuid}")
            
            # Comparaciones con strings
            print(f"  - Project ID (str) match: {str(session.project_id)} == {project_id_str} -> {str(session.project_id) == project_id_str}")
            print(f"  - User ID (str) match: {str(session.user_id)} == {user_id_str} -> {str(session.user_id) == user_id_str}")
            
            # Validación completa
            valid = (session.project_id == project_uuid and 
                    session.user_id == user_uuid)
            print(f"  - Validación completa: {valid}")
        else:
            print("  ❌ Sesión no encontrada")
            
            # Buscar todas las sesiones para ver qué hay
            all_query = select(InteractionEvent).where(
                InteractionEvent.interaction_type == "context_building"
            ).order_by(InteractionEvent.created_at.desc()).limit(5)
            
            all_result = await db.execute(all_query)
            all_sessions = all_result.scalars().all()
            
            print(f"\n📋 ÚLTIMAS 5 SESIONES CONTEXT_BUILDING:")
            for i, s in enumerate(all_sessions, 1):
                print(f"  {i}. {s.id} - Project: {s.project_id} - User: {s.user_id}")
        
        break

if __name__ == "__main__":
    asyncio.run(debug_specific_session()) 