from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task_template import TaskTemplate
from app.schemas.task_template import (
    TaskTemplateCreate,
    TaskTemplateUpdate,
    TaskTemplateResponse,
)

router = APIRouter(prefix="/api/task-templates", tags=["task-templates"])


@router.get("", response_model=list[TaskTemplateResponse])
async def list_task_templates(
    category: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """获取任务模版列表"""
    query = select(TaskTemplate).order_by(TaskTemplate.created_at.desc())
    if category:
        query = query.where(TaskTemplate.category == category)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=TaskTemplateResponse)
async def create_task_template(
    template_in: TaskTemplateCreate, db: AsyncSession = Depends(get_db)
):
    """创建任务模版"""
    template = TaskTemplate(**template_in.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """获取所有分类"""
    result = await db.execute(
        select(TaskTemplate.category).where(TaskTemplate.category.isnot(None)).distinct()
    )
    categories = [row[0] for row in result.all() if row[0]]
    return categories


@router.get("/{template_id}", response_model=TaskTemplateResponse)
async def get_task_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个任务模版"""
    result = await db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Task template not found")
    return template


@router.put("/{template_id}", response_model=TaskTemplateResponse)
async def update_task_template(
    template_id: int, template_in: TaskTemplateUpdate, db: AsyncSession = Depends(get_db)
):
    """更新任务模版"""
    result = await db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Task template not found")

    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/{template_id}")
async def delete_task_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """删除任务模版"""
    result = await db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Task template not found")

    await db.delete(template)
    await db.commit()
    return {"message": "Task template deleted"}
