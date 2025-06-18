#!/usr/bin/env python3
"""
Script para debuggear el problema de sesiones de contexto.
"""

import asyncio
import json
from uuid import UUID
from sqlmodel import select
from app.core.database import get_db
from app.models.models import InteractionEvent

async def debug_sessions():
    """Debuggea las sesiones en la base de datos."""
    
    async for db in get_db():
        print("🔍 DEBUGGING SESIONES DE CONTEXTO")
        print("=" * 50)
        
        # Buscar todas las sesiones de context_building
        query = select(InteractionEvent).where(
            InteractionEvent.interaction_type == "context_building"
        ).order_by(InteractionEvent.created_at.desc()).limit(10)
        
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        print(f"📊 Total de sesiones context_building encontradas: {len(sessions)}")
        
        for i, session in enumerate(sessions, 1):
            print(f"\n🔍 SESIÓN {i}:")
            print(f"  - ID: {session.id} (tipo: {type(session.id)})")
            print(f"  - Project ID: {session.project_id}")
            print(f"  - User ID: {session.user_id}")
            print(f"  - Tipo: {session.interaction_type}")
            print(f"  - Estado: {session.session_status}")
            print(f"  - Creado: {session.created_at}")
            print(f"  - Actualizado: {session.updated_at}")
            print(f"  - Eliminado: {session.deleted_at}")
            
            # Mostrar historial conversacional
            try:
                history = json.loads(session.ai_responses_json or "[]")
                print(f"  - Mensajes en historial: {len(history)}")
                for j, msg in enumerate(history):
                    print(f"    {j+1}. {msg.get('role', 'unknown')}: {msg.get('content', '')[:50]}...")
            except Exception as e:
                print(f"  - Error parseando historial: {e}")
        
        # Probar búsqueda específica con un ID
        if sessions:
            test_session = sessions[0]
            print(f"\n🧪 PRUEBA DE BÚSQUEDA ESPECÍFICA")
            print(f"Buscando sesión: {test_session.id}")
            
            # Buscar como string
            query_str = select(InteractionEvent).where(
                InteractionEvent.id == str(test_session.id),
                InteractionEvent.interaction_type == "context_building",
                InteractionEvent.deleted_at.is_(None)
            )
            result_str = await db.execute(query_str)
            found_str = result_str.scalar_one_or_none()
            print(f"Encontrado con string: {found_str is not None}")
            
            # Buscar como UUID
            query_uuid = select(InteractionEvent).where(
                InteractionEvent.id == test_session.id,
                InteractionEvent.interaction_type == "context_building",
                InteractionEvent.deleted_at.is_(None)
            )
            result_uuid = await db.execute(query_uuid)
            found_uuid = result_uuid.scalar_one_or_none()
            print(f"Encontrado con UUID: {found_uuid is not None}")
            
            # Buscar convirtiendo string a UUID
            try:
                test_uuid = UUID(str(test_session.id))
                query_converted = select(InteractionEvent).where(
                    InteractionEvent.id == test_uuid,
                    InteractionEvent.interaction_type == "context_building",
                    InteractionEvent.deleted_at.is_(None)
                )
                result_converted = await db.execute(query_converted)
                found_converted = result_converted.scalar_one_or_none()
                print(f"Encontrado con UUID convertido: {found_converted is not None}")
            except Exception as e:
                print(f"Error convirtiendo UUID: {e}")
        
        break

if __name__ == "__main__":
    asyncio.run(debug_sessions()) 