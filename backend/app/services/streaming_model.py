"""流式 ModelClient - 支持回调的 phone_agent 补丁版本"""

import time
import logging
from typing import Any, Callable

from openai import OpenAI
from phone_agent.model.client import ModelConfig, ModelResponse

logger = logging.getLogger(__name__)


class StreamingModelClient:
    """
    支持流式回调的 ModelClient。

    通过 token_callback 实时推送每个 token，实现打字机效果。
    """

    def __init__(
        self,
        config: ModelConfig | None = None,
        token_callback: Callable[[str, str], None] | None = None,
    ):
        """
        初始化流式客户端。

        Args:
            config: 模型配置
            token_callback: 流式回调函数，参数为 (phase, content)
                - phase: "thinking" 或 "action"
                - content: token 内容
        """
        self.config = config or ModelConfig()
        self.client = OpenAI(base_url=self.config.base_url, api_key=self.config.api_key)
        self.token_callback = token_callback

    def request(self, messages: list[dict[str, Any]]) -> ModelResponse:
        """
        发送请求并流式返回结果。
        """
        start_time = time.time()
        time_to_first_token = None
        time_to_thinking_end = None

        stream = self.client.chat.completions.create(
            messages=messages,
            model=self.config.model_name,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            frequency_penalty=self.config.frequency_penalty,
            extra_body=self.config.extra_body,
            stream=True,
        )

        raw_content = ""
        buffer = ""
        action_markers = ["finish(message=", "do(action="]
        in_action_phase = False
        first_token_received = False

        for chunk in stream:
            if len(chunk.choices) == 0:
                continue
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                raw_content += content

                # 记录首个 token 时间
                if not first_token_received:
                    time_to_first_token = time.time() - start_time
                    first_token_received = True

                if in_action_phase:
                    # 在 action 阶段，通过回调发送
                    if self.token_callback:
                        self.token_callback("action", content)
                    continue

                buffer += content

                # 检查是否遇到 action 标记
                marker_found = False
                for marker in action_markers:
                    if marker in buffer:
                        # 找到标记，发送之前的 thinking 部分
                        thinking_part = buffer.split(marker, 1)[0]
                        if thinking_part and self.token_callback:
                            self.token_callback("thinking", thinking_part)

                        # 发送 action 标记本身
                        if self.token_callback:
                            self.token_callback("action", marker)

                        in_action_phase = True
                        marker_found = True

                        if time_to_thinking_end is None:
                            time_to_thinking_end = time.time() - start_time

                        break

                if marker_found:
                    continue

                # 检查 buffer 末尾是否可能是标记的前缀
                is_potential_marker = False
                for marker in action_markers:
                    for i in range(1, len(marker)):
                        if buffer.endswith(marker[:i]):
                            is_potential_marker = True
                            break
                    if is_potential_marker:
                        break

                if not is_potential_marker:
                    # 安全发送 buffer
                    if buffer and self.token_callback:
                        self.token_callback("thinking", buffer)
                    buffer = ""

        # 计算总时间
        total_time = time.time() - start_time

        # 解析 thinking 和 action
        thinking, action = self._parse_response(raw_content)

        return ModelResponse(
            thinking=thinking,
            action=action,
            raw_content=raw_content,
            time_to_first_token=time_to_first_token,
            time_to_thinking_end=time_to_thinking_end,
            total_time=total_time,
        )

    def _parse_response(self, content: str) -> tuple[str, str]:
        """解析响应内容为 thinking 和 action 部分"""
        # 规则 1: 检查 finish(message=
        if "finish(message=" in content:
            parts = content.split("finish(message=", 1)
            thinking = parts[0].strip()
            action = "finish(message=" + parts[1]
            return thinking, action

        # 规则 2: 检查 do(action=
        if "do(action=" in content:
            parts = content.split("do(action=", 1)
            thinking = parts[0].strip()
            action = "do(action=" + parts[1]
            return thinking, action

        # 规则 3: 回退到 XML 标签解析
        if "<answer>" in content:
            parts = content.split("<answer>", 1)
            thinking = parts[0].replace("<think>", "").replace("</think>", "").strip()
            action = parts[1].replace("</answer>", "").strip()
            return thinking, action

        # 规则 4: 没有找到标记
        return "", content


def patch_phone_agent(token_callback: Callable[[str, str], None] | None = None):
    """
    Monkey patch phone_agent 的 ModelClient。

    使用方法：
        from app.services.streaming_model import patch_phone_agent

        def my_callback(phase, content):
            print(f"[{phase}] {content}", end="", flush=True)

        patch_phone_agent(my_callback)

        # 之后创建的 PhoneAgent 将使用流式回调
        agent = PhoneAgent(...)
    """
    import phone_agent.model.client as client_module
    import phone_agent.model as model_module
    import phone_agent.agent as agent_module

    # 保存原始类
    original_model_client = client_module.ModelClient

    # 创建带回调的版本
    class PatchedModelClient(StreamingModelClient):
        def __init__(self, config=None):
            super().__init__(config, token_callback)

    # 替换所有可能的引用位置
    client_module.ModelClient = PatchedModelClient
    model_module.ModelClient = PatchedModelClient
    agent_module.ModelClient = PatchedModelClient  # 关键：替换 agent 模块中的引用

    logger.info("[patch_phone_agent] 已应用流式补丁到所有模块")

    return original_model_client


def unpatch_phone_agent(original_class):
    """恢复原始的 ModelClient"""
    import phone_agent.model.client as client_module
    import phone_agent.model as model_module
    import phone_agent.agent as agent_module
    client_module.ModelClient = original_class
    model_module.ModelClient = original_class
    agent_module.ModelClient = original_class
    logger.info("[unpatch_phone_agent] 已恢复原始 ModelClient")
