from typing import List, Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


async def create_project(
    db: AsyncSession, *, obj_in: ProjectCreate, user_id: UUID
) -> Project:
    db_obj = Project(
        user_id=user_id,
        name=obj_in.name,
        description=obj_in.description,
        moderator_personality=obj_in.moderator_personality,
        moderator_temperature=obj_in.moderator_temperature,
        moderator_length_penalty=obj_in.moderator_length_penalty,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_project(db: AsyncSession, id: UUID) -> Optional[Project]:
    statement = select(Project).where(Project.id == id)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_projects_by_user(
    db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100
) -> List[Project]:
    statement = (
        select(Project)
        .where(Project.user_id == user_id)
        .where(Project.deleted_at.is_(None))
        .offset(skip)
        .limit(limit)
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(statement)
    return result.scalars().all()


async def update_project(
    db: AsyncSession,
    *,
    db_obj: Project,
    obj_in: ProjectUpdate
) -> Project:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_project(db: AsyncSession, *, id: UUID) -> Project:
    statement = select(Project).where(Project.id == id)
    result = await db.execute(statement)
    project = result.scalar_one_or_none()
    if project:
        await db.delete(project)
        await db.commit()
    return project 