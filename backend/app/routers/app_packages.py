from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.app_package import AppPackage
from app.schemas.app_package import (
    AppPackageCreate,
    AppPackageUpdate,
    AppPackageResponse,
)

router = APIRouter(prefix="/api/app-packages", tags=["app-packages"])


@router.get("", response_model=list[AppPackageResponse])
async def list_app_packages(db: AsyncSession = Depends(get_db)):
    """获取自定义 APP 包名列表"""
    result = await db.execute(select(AppPackage).order_by(AppPackage.app_name))
    return result.scalars().all()


@router.post("", response_model=AppPackageResponse)
async def create_app_package(
    data: AppPackageCreate, db: AsyncSession = Depends(get_db)
):
    """创建 APP 包名映射"""
    # 检查是否已存在
    result = await db.execute(
        select(AppPackage).where(AppPackage.app_name == data.app_name)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="App name already exists")

    app_package = AppPackage(**data.model_dump())
    db.add(app_package)
    await db.commit()
    await db.refresh(app_package)
    return app_package


@router.get("/{package_id}", response_model=AppPackageResponse)
async def get_app_package(package_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个 APP 包名映射"""
    result = await db.execute(
        select(AppPackage).where(AppPackage.id == package_id)
    )
    app_package = result.scalar_one_or_none()
    if not app_package:
        raise HTTPException(status_code=404, detail="App package not found")
    return app_package


@router.put("/{package_id}", response_model=AppPackageResponse)
async def update_app_package(
    package_id: int,
    data: AppPackageUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新 APP 包名映射"""
    result = await db.execute(
        select(AppPackage).where(AppPackage.id == package_id)
    )
    app_package = result.scalar_one_or_none()
    if not app_package:
        raise HTTPException(status_code=404, detail="App package not found")

    update_data = data.model_dump(exclude_unset=True)

    # 如果更新 app_name，检查是否与其他记录冲突
    if "app_name" in update_data and update_data["app_name"] != app_package.app_name:
        result = await db.execute(
            select(AppPackage).where(AppPackage.app_name == update_data["app_name"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="App name already exists")

    for field, value in update_data.items():
        setattr(app_package, field, value)

    await db.commit()
    await db.refresh(app_package)
    return app_package


@router.delete("/{package_id}")
async def delete_app_package(package_id: int, db: AsyncSession = Depends(get_db)):
    """删除 APP 包名映射"""
    result = await db.execute(
        select(AppPackage).where(AppPackage.id == package_id)
    )
    app_package = result.scalar_one_or_none()
    if not app_package:
        raise HTTPException(status_code=404, detail="App package not found")

    await db.delete(app_package)
    await db.commit()
    return {"message": "App package deleted"}
