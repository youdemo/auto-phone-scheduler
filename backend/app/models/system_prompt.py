from datetime import datetime
from sqlalchemy import String, Boolean, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SystemPrompt(Base):
    """系统提示词模型，针对不同设备配置系统级提示词"""
    __tablename__ = "system_prompts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 设备匹配规则 (支持通配符 * )
    device_serial: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Prompt 内容
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)  # 系统提示词
    prefix_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)  # 指令前缀
    suffix_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)  # 指令后缀

    # 优先级 (数字越大优先级越高)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
