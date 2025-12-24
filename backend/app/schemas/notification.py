from pydantic import BaseModel
from app.models.notification import NotificationType


class NotificationChannelBase(BaseModel):
    type: NotificationType
    name: str
    config: dict
    enabled: bool = True


class NotificationChannelCreate(NotificationChannelBase):
    pass


class NotificationChannelUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None
    enabled: bool | None = None


class NotificationChannelResponse(NotificationChannelBase):
    id: int

    class Config:
        from_attributes = True
