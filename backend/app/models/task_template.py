from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class TaskTemplate(Base):
    """任务模版模型，可以快速创建任务或在创建任务时选择"""
    __tablename__ = "task_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 任务模版内容
    command: Mapped[str] = mapped_column(Text, nullable=False)  # Prompt 指令模版

    # 可选的默认 cron 表达式
    default_cron: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 分类标签
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 图标 (lucide icon name)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
