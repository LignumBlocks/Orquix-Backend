import asyncio
from app.core.database import get_db
from app.models.models import Project, User
from sqlalchemy import select
from uuid import uuid4

async def check_and_create_test_data():
    async for db in get_db():
        # Verificar usuarios
        users_result = await db.execute(select(User))
        users = users_result.scalars().all()
        print(f'Usuarios encontrados: {len(users)}')
        
        # Si no hay usuarios, crear uno de prueba
        if not users:
            test_user = User(
                id="550e8400-e29b-41d4-a716-446655440000",
                email="dev@orquix.com",
                name="Developer User",
                google_id="dev_google_123",
                avatar_url="https://example.com/avatar.png"
            )
            db.add(test_user)
            await db.commit()
            await db.refresh(test_user)
            print(f'✅ Usuario de prueba creado: {test_user.name} ({test_user.id})')
            users = [test_user]
        
        # Verificar proyectos  
        projects_result = await db.execute(select(Project))
        projects = projects_result.scalars().all()
        print(f'Proyectos encontrados: {len(projects)}')
        
        if projects:
            for p in projects:
                print(f'  - {p.name} ({p.id})')
        
        # Si no hay proyectos, crear uno de prueba
        if not projects and users:
            user = users[0]
            test_project_id = "0fa97bbe-34d6-488c-b085-bd4d70b90316"
            test_project = Project(
                id=test_project_id,
                user_id=user.id,
                name='Proyecto de Prueba Context Builder',
                description='Proyecto para probar la construcción de contexto'
            )
            db.add(test_project)
            await db.commit()
            await db.refresh(test_project)
            print(f'✅ Proyecto de prueba creado: {test_project.name} ({test_project.id})')
        
        break

if __name__ == "__main__":
    asyncio.run(check_and_create_test_data()) 