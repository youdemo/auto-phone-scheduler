from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import Task
from app.models.execution import Execution, ExecutionStatus
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.scheduler import SchedulerService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    """获取任务列表"""
    result = await db.execute(select(Task).order_by(Task.created_at.desc()))
    tasks = result.scalars().all()

    scheduler = SchedulerService.get_instance()
    response = []
    for task in tasks:
        task_dict = TaskResponse.model_validate(task)
        next_run = scheduler.get_next_run_time(task.id)
        task_dict.next_run = next_run.isoformat() if next_run else None
        response.append(task_dict)

    return response


@router.post("", response_model=TaskResponse)
async def create_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db)):
    """创建任务"""
    task = Task(**task_in.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 添加到调度器
    scheduler = SchedulerService.get_instance()
    scheduler.add_job(task)

    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    scheduler = SchedulerService.get_instance()
    response = TaskResponse.model_validate(task)
    next_run = scheduler.get_next_run_time(task.id)
    response.next_run = next_run.isoformat() if next_run else None

    return response


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int, task_in: TaskUpdate, db: AsyncSession = Depends(get_db)
):
    """更新任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    # 更新调度器
    scheduler = SchedulerService.get_instance()
    if task.enabled:
        scheduler.add_job(task)
    else:
        scheduler.remove_job(task.id)

    return task


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """删除任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 从调度器移除
    scheduler = SchedulerService.get_instance()
    scheduler.remove_job(task.id)

    await db.delete(task)
    await db.commit()

    return {"message": "Task deleted"}


@router.post("/{task_id}/run")
async def run_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """立即执行任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 先创建执行记录
    execution = Execution(
        task_id=task_id,
        status=ExecutionStatus.RUNNING,
        started_at=datetime.utcnow(),
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # 启动后台任务执行
    scheduler = SchedulerService.get_instance()
    background_tasks.add_task(scheduler.run_task_with_execution, task_id, execution.id)

    return {"message": "Task execution started", "execution_id": execution.id}
