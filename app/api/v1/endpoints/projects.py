from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.crud import project as project_crud
from app.schemas.project import Project, ProjectCreate, ProjectUpdate

router = APIRouter()


@router.post("/", response_model=Project)
async def create_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_in: ProjectCreate,
    user_id: UUID,  # TODO: Get from JWT token
) -> Project:
    """
    Create new project.
    """
    project = await project_crud.create_project(db=db, obj_in=project_in, user_id=user_id)
    return project


@router.get("/", response_model=List[Project])
async def read_projects(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: UUID,  # TODO: Get from JWT token
) -> List[Project]:
    """
    Retrieve projects.
    """
    projects = await project_crud.get_projects_by_user(
        db=db, user_id=user_id, skip=skip, limit=limit
    )
    return projects


@router.get("/{project_id}", response_model=Project)
async def read_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: UUID,
) -> Project:
    """
    Get project by ID.
    """
    project = await project_crud.get_project(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=Project)
async def update_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: UUID,
    project_in: ProjectUpdate,
) -> Project:
    """
    Update project.
    """
    project = await project_crud.get_project(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project = await project_crud.update_project(db=db, db_obj=project, obj_in=project_in)
    return project


@router.delete("/{project_id}", response_model=Project)
async def delete_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: UUID,
) -> Project:
    """
    Delete project.
    """
    project = await project_crud.get_project(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project = await project_crud.delete_project(db=db, id=project_id)
    return project 