from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./scheduler.db"

    # ADB - 连接远程 ADB server（用于 Docker）
    # 格式: host:port，留空则使用本地 adb
    adb_server_socket: str = ""

    # AutoGLM
    # 注意: 需要使用专门训练的 AutoGLM 模型 (如 autoglm-phone-9b)
    # glm-4v-flash 等通用模型可能无法正确输出 action 格式
    autoglm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    autoglm_api_key: str = ""
    autoglm_model: str = "autoglm-phone-9b"
    autoglm_max_steps: int = 100
    autoglm_lang: str = "cn"

    # Recordings
    recordings_dir: str = "./recordings"

    # Notifications
    dingtalk_webhook: str = ""
    dingtalk_secret: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
