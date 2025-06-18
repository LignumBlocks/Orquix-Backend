#!/usr/bin/env python3
"""
Script de prueba para verificar la continuidad conversacional simplificada.

Prueba los 3 modos:
- auto: Asume continuidad si hay interacciones previas
- continue: Fuerza continuidad
- new: Fuerza tema nuevo
"""

import asyncio
import sys
import os
from uuid import UUID, uuid4

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.followup_interpreter import FollowUpInterpreter
from app.database.database import get_db
from app.database.models import InteractionEvent
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

async def test_simplified_continuity():
    """Prueba la lógica simplificada de continuidad conversacional"""
    
    # IDs de prueba
    project_id = UUID("12345678-1234-5678-9012-123456789012")
    user_id = UUID("87654321-4321-8765-2109-876543210987")
    
    print("🧪 PRUEBA: Continuidad Conversacional Simplificada")
    print("=" * 60)
    
    # Crear instancia del intérprete
    async for db in get_db():
        followup_interpreter = FollowUpInterpreter(db)
        
        # CASO 1: Proyecto sin interacciones previas
        print("\n📝 CASO 1: Proyecto nuevo (sin interacciones)")
        print("-" * 40)
        
        for mode in ["auto", "continue", "new"]:
            try:
                result = await followup_interpreter.handle_followup(
                    user_prompt="¿Qué algoritmos utilizar?",
                    project_id=project_id,
                    user_id=user_id,
                    conversation_mode=mode
                )
                print(f"Modo '{mode}': {result.query_type.value}")
            except Exception as e:
                print(f"Modo '{mode}': ERROR - {e}")
        
        # CASO 2: Simular proyecto con interacciones previas
        print("\n📝 CASO 2: Proyecto con interacciones previas")
        print("-" * 40)
        
        # Crear una interacción ficticia en la base de datos
        fake_interaction = InteractionEvent(
            id=uuid4(),
            project_id=project_id,
            user_id=user_id,
            user_prompt="Necesito hacer un MVP para resumir noticias",
            ai_responses=[],
            moderator_synthesis={"synthesis_text": "Te ayudo con el MVP de noticias"},
            context_used=False,
            processing_time_ms=1000,
            created_at=datetime.utcnow()
        )
        
        try:
            db.add(fake_interaction)
            await db.commit()
            print("✅ Interacción ficticia creada")
            
            # Probar los 3 modos con interacciones previas
            for mode in ["auto", "continue", "new"]:
                try:
                    result = await followup_interpreter.handle_followup(
                        user_prompt="¿Qué algoritmos utilizar?",
                        project_id=project_id,
                        user_id=user_id,
                        conversation_mode=mode
                    )
                    print(f"Modo '{mode}': {result.query_type.value}")
                except Exception as e:
                    print(f"Modo '{mode}': ERROR - {e}")
                    
        except Exception as e:
            print(f"❌ Error creando interacción ficticia: {e}")
        finally:
            # Limpiar la base de datos
            try:
                await db.rollback()
                print("🧹 Base de datos limpiada")
            except:
                pass
        
        break  # Solo usar la primera sesión de DB

if __name__ == "__main__":
    asyncio.run(test_simplified_continuity()) 