from pydantic import BaseModel


class DeviceInfo(BaseModel):
    serial: str
    status: str
    model: str | None = None
    product: str | None = None
