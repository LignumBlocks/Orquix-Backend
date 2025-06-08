import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.core.database import engine
from app.models.models import User

async def create_mock_user():
    async with AsyncSession(engine) as db:
        # Verificar si el usuario ya existe
        statement = select(User).where(User.id == '550e8400-e29b-41d4-a716-446655440000')
        result = await db.exec(statement)
        existing_user = result.first()
        
        if not existing_user:
            # Crear el usuario mock con todos los campos requeridos
            user = User(
                id='550e8400-e29b-41d4-a716-446655440000',
                email='dev@orquix.com',
                name='Developer User',
                google_id='mock-google-id-dev-user',
                avatar_url='https://via.placeholder.com/150'
            )
            db.add(user)
            await db.commit()
            print('✅ Usuario mock creado exitosamente')
            print(f'   ID: {user.id}')
            print(f'   Email: {user.email}')
            print(f'   Nombre: {user.name}')
        else:
            print('ℹ️ Usuario mock ya existe')
            print(f'   ID: {existing_user.id}')
            print(f'   Email: {existing_user.email}')
            print(f'   Nombre: {existing_user.name}')

if __name__ == "__main__":
    asyncio.run(create_mock_user()) 