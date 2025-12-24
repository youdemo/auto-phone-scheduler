import fnmatch
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.system_prompt import SystemPrompt
from app.schemas.system_prompt import (
    SystemPromptCreate,
    SystemPromptUpdate,
    SystemPromptResponse,
)

router = APIRouter(prefix="/api/system-prompts", tags=["system-prompts"])


@router.get("", response_model=list[SystemPromptResponse])
async def list_system_prompts(db: AsyncSession = Depends(get_db)):
    """获取所有系统提示词列表"""
    result = await db.execute(
        select(SystemPrompt).order_by(SystemPrompt.priority.desc(), SystemPrompt.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=SystemPromptResponse)
async def create_system_prompt(
    prompt_in: SystemPromptCreate, db: AsyncSession = Depends(get_db)
):
    """创建系统提示词"""
    prompt = SystemPrompt(**prompt_in.model_dump())
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.get("/{prompt_id}", response_model=SystemPromptResponse)
async def get_system_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个系统提示词"""
    result = await db.execute(select(SystemPrompt).where(SystemPrompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="System prompt not found")
    return prompt


@router.put("/{prompt_id}", response_model=SystemPromptResponse)
async def update_system_prompt(
    prompt_id: int, prompt_in: SystemPromptUpdate, db: AsyncSession = Depends(get_db)
):
    """更新系统提示词"""
    result = await db.execute(select(SystemPrompt).where(SystemPrompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="System prompt not found")

    update_data = prompt_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prompt, field, value)

    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}")
async def delete_system_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    """删除系统提示词"""
    result = await db.execute(select(SystemPrompt).where(SystemPrompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="System prompt not found")

    await db.delete(prompt)
    await db.commit()
    return {"message": "System prompt deleted"}


@router.get("/match/{device_serial}")
async def get_matching_prompts(
    device_serial: str,
    device_model: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取匹配指定设备的所有提示词 (按优先级排序)"""
    result = await db.execute(
        select(SystemPrompt)
        .where(SystemPrompt.enabled == True)
        .order_by(SystemPrompt.priority.desc())
    )
    all_prompts = result.scalars().all()

    matched_prompts = []
    for prompt in all_prompts:
        serial_match = True
        if prompt.device_serial:
            serial_match = fnmatch.fnmatch(device_serial, prompt.device_serial)

        model_match = True
        if prompt.device_model and device_model:
            model_match = fnmatch.fnmatch(device_model, prompt.device_model)

        if serial_match and model_match:
            matched_prompts.append(prompt)

    return matched_prompts


@router.post("/preview")
async def preview_prompt(
    device_serial: str,
    command: str,
    device_model: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """预览应用提示词后的最终 prompt"""
    result = await db.execute(
        select(SystemPrompt)
        .where(SystemPrompt.enabled == True)
        .order_by(SystemPrompt.priority.desc())
    )
    all_prompts = result.scalars().all()

    system_prompt = ""
    prefix_prompt = ""
    suffix_prompt = ""

    for prompt in all_prompts:
        serial_match = True
        if prompt.device_serial:
            serial_match = fnmatch.fnmatch(device_serial, prompt.device_serial)

        model_match = True
        if prompt.device_model and device_model:
            model_match = fnmatch.fnmatch(device_model, prompt.device_model)

        if serial_match and model_match:
            if prompt.system_prompt:
                system_prompt = prompt.system_prompt
            if prompt.prefix_prompt:
                prefix_prompt = prompt.prefix_prompt
            if prompt.suffix_prompt:
                suffix_prompt = prompt.suffix_prompt

    final_command = command
    if prefix_prompt:
        final_command = f"{prefix_prompt}\n{final_command}"
    if suffix_prompt:
        final_command = f"{final_command}\n{suffix_prompt}"

    return {
        "original_command": command,
        "system_prompt": system_prompt,
        "final_command": final_command,
    }
