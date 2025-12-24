import hashlib
import hmac
import base64
import time
import urllib.parse
from abc import ABC, abstractmethod

import httpx

from app.models.notification import NotificationType


class NotifierBase(ABC):
    """通知器基类"""

    @abstractmethod
    async def send(self, title: str, content: str) -> bool:
        """发送通知"""
        pass

    @abstractmethod
    async def test(self) -> bool:
        """测试通知连接"""
        pass


class DingTalkNotifier(NotifierBase):
    """钉钉机器人通知"""

    def __init__(self, webhook: str, secret: str = ""):
        self.webhook = webhook
        self.secret = secret

    def _sign(self) -> tuple[str, str]:
        """生成签名"""
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode("utf-8")
        string_to_sign = f"{timestamp}\n{self.secret}"
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, sign

    async def send(self, title: str, content: str) -> bool:
        """发送钉钉消息"""
        url = self.webhook
        if self.secret:
            timestamp, sign = self._sign()
            url = f"{self.webhook}&timestamp={timestamp}&sign={sign}"

        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"### {title}\n\n{content}",
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, timeout=10)
                result = response.json()
                return result.get("errcode") == 0
        except Exception:
            return False

    async def test(self) -> bool:
        """测试钉钉连接"""
        return await self.send("测试通知", "这是一条测试消息，用于验证钉钉机器人配置是否正确。")


class TelegramNotifier(NotifierBase):
    """Telegram Bot 通知"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_base = f"https://api.telegram.org/bot{bot_token}"

    async def send(self, title: str, content: str) -> bool:
        """发送 Telegram 消息"""
        url = f"{self.api_base}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": f"*{title}*\n\n{content}",
            "parse_mode": "Markdown",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, timeout=10)
                result = response.json()
                return result.get("ok", False)
        except Exception:
            return False

    async def test(self) -> bool:
        """测试 Telegram 连接"""
        return await self.send("测试通知", "这是一条测试消息，用于验证 Telegram Bot 配置是否正确。")


class NotifierService:
    """通知服务"""

    @staticmethod
    def create_notifier(channel_type: NotificationType, config: dict) -> NotifierBase:
        """根据配置创建通知器"""
        if channel_type == NotificationType.DINGTALK:
            return DingTalkNotifier(
                webhook=config.get("webhook", ""),
                secret=config.get("secret", ""),
            )
        elif channel_type == NotificationType.TELEGRAM:
            return TelegramNotifier(
                bot_token=config.get("bot_token", ""),
                chat_id=config.get("chat_id", ""),
            )
        else:
            raise ValueError(f"Unsupported notification type: {channel_type}")

    async def send_notification(
        self,
        channel_type: NotificationType,
        config: dict,
        title: str,
        content: str,
    ) -> bool:
        """发送通知"""
        notifier = self.create_notifier(channel_type, config)
        return await notifier.send(title, content)

    async def test_notification(
        self,
        channel_type: NotificationType,
        config: dict,
    ) -> bool:
        """测试通知"""
        notifier = self.create_notifier(channel_type, config)
        return await notifier.test()
