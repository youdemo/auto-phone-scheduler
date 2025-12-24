import asyncio
import fnmatch
from datetime import datetime, timezone
from typing import Callable, Awaitable, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.system_prompt import SystemPrompt

# 回调类型：支持同步或异步回调
StepCallback = Callable[[dict], Union[None, Awaitable[None]]]

settings = get_settings()


class AutoGLMService:
    """AutoGLM 客户端封装，用于执行手机自动化任务"""

    def __init__(self):
        self.base_url = settings.autoglm_base_url
        self.api_key = settings.autoglm_api_key
        self.model = settings.autoglm_model
        self.max_steps = settings.autoglm_max_steps
        self.lang = settings.autoglm_lang

    async def reload_settings(self, db: AsyncSession):
        """从数据库重新加载设置"""
        from app.models.settings import SystemSettings

        result = await db.execute(select(SystemSettings))
        db_settings = {s.key: s.value for s in result.scalars().all()}

        if db_settings.get("autoglm_base_url"):
            self.base_url = db_settings["autoglm_base_url"]
        if db_settings.get("autoglm_api_key"):
            self.api_key = db_settings["autoglm_api_key"]
        if db_settings.get("autoglm_model"):
            self.model = db_settings["autoglm_model"]
        if db_settings.get("autoglm_max_steps"):
            self.max_steps = int(db_settings["autoglm_max_steps"])

    async def get_system_prompts(
        self,
        db: AsyncSession,
        device_serial: str,
        device_model: str | None = None,
    ) -> tuple[str, str, str]:
        """
        获取匹配设备的系统提示词

        Returns:
            (system_prompt, prefix_prompt, suffix_prompt)
        """
        result = await db.execute(
            select(SystemPrompt)
            .where(SystemPrompt.enabled == True)
            .order_by(SystemPrompt.priority.asc())  # 低优先级先处理，高优先级后覆盖
        )
        all_prompts = result.scalars().all()

        system_prompt = ""
        prefix_prompt = ""
        suffix_prompt = ""

        for prompt in all_prompts:
            # 检查设备序列号匹配 (支持通配符)
            serial_match = True
            if prompt.device_serial:
                serial_match = fnmatch.fnmatch(device_serial, prompt.device_serial)

            # 检查设备型号匹配
            model_match = True
            if prompt.device_model and device_model:
                model_match = fnmatch.fnmatch(device_model, prompt.device_model)

            if serial_match and model_match:
                # 应用提示词 (高优先级会覆盖低优先级)
                if prompt.system_prompt:
                    system_prompt = prompt.system_prompt
                if prompt.prefix_prompt:
                    prefix_prompt = prompt.prefix_prompt
                if prompt.suffix_prompt:
                    suffix_prompt = prompt.suffix_prompt

        return system_prompt, prefix_prompt, suffix_prompt

    def apply_prompt_rules(
        self,
        command: str,
        prefix_prompt: str,
        suffix_prompt: str,
    ) -> str:
        """应用 prompt 规则到命令"""
        final_command = command
        if prefix_prompt:
            final_command = f"{prefix_prompt}\n{final_command}"
        if suffix_prompt:
            final_command = f"{final_command}\n{suffix_prompt}"
        return final_command

    async def execute_task(
        self,
        command: str,
        step_callback: StepCallback | None = None,
        db: AsyncSession | None = None,
        device_serial: str | None = None,
        device_model: str | None = None,
    ) -> dict:
        """
        执行 AutoGLM 任务

        Args:
            command: 自然语言指令
            step_callback: 每个步骤完成时的回调函数
            db: 数据库会话 (用于获取 prompt 规则)
            device_serial: 设备序列号
            device_model: 设备型号

        Returns:
            执行结果，包含所有步骤信息
        """
        steps = []
        final_command = command
        system_prompt = ""

        try:
            # 如果提供了数据库会话和设备信息，获取并应用系统提示词
            if db and device_serial:
                system_prompt, prefix_prompt, suffix_prompt = await self.get_system_prompts(
                    db, device_serial, device_model
                )
                final_command = self.apply_prompt_rules(command, prefix_prompt, suffix_prompt)

            # 重新加载数据库中的设置
            if db:
                await self.reload_settings(db)

            # 使用 PhoneAgent 执行任务
            result = await self._run_agent(
                final_command, steps, step_callback, system_prompt, device_serial
            )
            return {
                "success": True,
                "steps": steps,
                "result": result,
                "original_command": command,
                "final_command": final_command,
                "system_prompt": system_prompt,
            }
        except Exception as e:
            return {
                "success": False,
                "steps": steps,
                "error": str(e),
                "original_command": command,
                "final_command": final_command,
            }

    async def _run_agent(
        self,
        command: str,
        steps: list,
        callback: StepCallback | None,
        custom_system_prompt: str = "",
        device_id: str | None = None,
    ) -> str:
        """运行 PhoneAgent"""
        from phone_agent import PhoneAgent
        from phone_agent.model import ModelConfig
        from phone_agent.agent import AgentConfig
        from phone_agent.config import get_system_prompt

        # 在线程池中运行同步的 agent
        def run_sync():
            model_config = ModelConfig(
                base_url=self.base_url,
                api_key=self.api_key,
                model_name=self.model,
                max_tokens=3000,           # 足够的输出长度
                temperature=0.0,           # 确定性输出，避免重复
                top_p=0.85,                # 控制采样多样性
                frequency_penalty=0.2,     # 惩罚重复 token
            )

            # 构建系统提示词：默认提示词 + 自定义提示词（附加而非替换）
            final_system_prompt = get_system_prompt(self.lang)
            if custom_system_prompt:
                final_system_prompt = f"{final_system_prompt}\n\n# 额外规则\n{custom_system_prompt}"

            # 构建 agent 配置
            agent_config = AgentConfig(
                max_steps=self.max_steps,
                device_id=device_id,
                lang=self.lang,
                system_prompt=final_system_prompt,
                verbose=True,
            )

            agent = PhoneAgent(
                model_config=model_config,
                agent_config=agent_config,
            )

            result = agent.run(command)

            # 从 agent 获取步骤信息并返回
            step_list = []
            for ctx in agent.context:
                if ctx.get("role") == "assistant":
                    step_info = {
                        "step": len(step_list) + 1,
                        "action": ctx.get("content", "")[:100] if ctx.get("content") else "",
                        "description": ctx.get("content", ""),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    step_list.append(step_info)

            return result, step_list

        # 使用线程池执行同步代码
        loop = asyncio.get_event_loop()
        result, step_list = await loop.run_in_executor(None, run_sync)

        # 在异步上下文中处理步骤和回调
        for step_info in step_list:
            steps.append(step_info)
            if callback:
                # 支持异步回调
                cb_result = callback(step_info)
                if asyncio.iscoroutine(cb_result):
                    await cb_result

        return result

    async def check_connection(self) -> bool:
        """检查 AutoGLM 服务是否可用"""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10,
                )
                return response.status_code == 200
        except Exception:
            return False
