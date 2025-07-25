from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    name: str
    description: str
    moderator_personality: str = "Analytical"
    moderator_temperature: float = 0.7
    moderator_length_penalty: float = 0.5

class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    name: Optional[str] = None
    description: Optional[str] = None
    moderator_personality: Optional[str] = None
    moderator_temperature: Optional[float] = None
    moderator_length_penalty: Optional[float] = None
    archived_at: Optional[datetime] = None


class ProjectInDBBase(ProjectBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Project(ProjectInDBBase):
    pass


class ProjectInDB(ProjectInDBBase):
    pass 