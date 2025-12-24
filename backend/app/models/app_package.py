from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AppPackage(Base):
    """自定义 APP 包名映射"""
    __tablename__ = "app_packages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    app_name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    package_name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
