from datetime import datetime
from pydantic import BaseModel, Field


class TaskTemplateBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = None
    command: str
    default_cron: str | None = Field(None, max_length=100)
    category: str | None = Field(None, max_length=50)
    icon: str | None = Field(None, max_length=50)


class TaskTemplateCreate(TaskTemplateBase):
    pass


class TaskTemplateUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    command: str | None = None
    default_cron: str | None = None
    category: str | None = None
    icon: str | None = None


class TaskTemplateResponse(TaskTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
