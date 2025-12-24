from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import NotificationChannel, NotificationType
from app.schemas.notification import (
    NotificationChannelCreate,
    NotificationChannelUpdate,
    NotificationChannelResponse,
)
from app.services.notifier import NotifierService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationChannelResponse])
async def list_channels(db: AsyncSession = Depends(get_db)):
    """获取通知渠道列表"""
    result = await db.execute(select(NotificationChannel))
    return result.scalars().all()


@router.post("", response_model=NotificationChannelResponse)
async def create_channel(
    channel_in: NotificationChannelCreate, db: AsyncSession = Depends(get_db)
):
    """创建通知渠道"""
    channel = NotificationChannel(**channel_in.model_dump())
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return channel


@router.get("/{channel_id}", response_model=NotificationChannelResponse)
async def get_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个通知渠道"""
    result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.put("/{channel_id}", response_model=NotificationChannelResponse)
async def update_channel(
    channel_id: int,
    channel_in: NotificationChannelUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新通知渠道"""
    result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    update_data = channel_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(channel, field, value)

    await db.commit()
    await db.refresh(channel)
    return channel


@router.delete("/{channel_id}")
async def delete_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    """删除通知渠道"""
    result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    await db.delete(channel)
    await db.commit()
    return {"message": "Channel deleted"}


@router.post("/{channel_id}/test")
async def test_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    """测试通知渠道"""
    result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    notifier = NotifierService()
    success = await notifier.test_notification(
        NotificationType(channel.type), channel.config
    )

    if success:
        return {"message": "Test notification sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test notification")
