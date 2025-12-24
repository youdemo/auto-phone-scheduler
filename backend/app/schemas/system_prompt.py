from datetime import datetime
from pydantic import BaseModel, Field


class SystemPromptBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = None
    device_serial: str | None = Field(None, max_length=100)
    device_model: str | None = Field(None, max_length=100)
    system_prompt: str | None = None
    prefix_prompt: str | None = None
    suffix_prompt: str | None = None
    priority: int = 0
    enabled: bool = True


class SystemPromptCreate(SystemPromptBase):
    pass


class SystemPromptUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    device_serial: str | None = None
    device_model: str | None = None
    system_prompt: str | None = None
    prefix_prompt: str | None = None
    suffix_prompt: str | None = None
    priority: int | None = None
    enabled: bool | None = None


class SystemPromptResponse(SystemPromptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
