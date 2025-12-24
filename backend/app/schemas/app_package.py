from datetime import datetime
from pydantic import BaseModel


class AppPackageBase(BaseModel):
    app_name: str
    package_name: str


class AppPackageCreate(AppPackageBase):
    pass


class AppPackageUpdate(BaseModel):
    app_name: str | None = None
    package_name: str | None = None


class AppPackageResponse(AppPackageBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
