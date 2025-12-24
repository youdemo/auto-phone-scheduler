"""ADB 工具模块 - 支持连接远程 ADB server"""
import asyncio
import os
from typing import Sequence

from app.config import get_settings


def _parse_adb_socket() -> tuple[str | None, str | None]:
    """解析 ADB server 地址，返回 (host, port) 或 (None, None)"""
    settings = get_settings()
    adb_socket = os.environ.get("ADB_SERVER_SOCKET") or settings.adb_server_socket

    if adb_socket:
        # 解析 tcp:host:port 格式
        if adb_socket.startswith("tcp:"):
            host_port = adb_socket[4:]
        else:
            host_port = adb_socket

        if ":" in host_port:
            host, port = host_port.rsplit(":", 1)
            return host, port

    return None, None


def get_adb_host() -> str:
    """获取 ADB server 所在主机地址（用于端口转发连接）"""
    host, _ = _parse_adb_socket()
    return host or "localhost"


def get_adb_command() -> list[str]:
    """获取 ADB 命令前缀（包含远程 server 配置）"""
    host, port = _parse_adb_socket()

    if host and port:
        return ["adb", "-H", host, "-P", port]

    return ["adb"]


async def run_adb(*args: str, serial: str | None = None) -> tuple[bytes, bytes]:
    """运行 ADB 命令"""
    cmd = get_adb_command()
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(args)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    return await process.communicate()


async def run_adb_exec(
    *args: str,
    serial: str | None = None,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
) -> asyncio.subprocess.Process:
    """创建 ADB 子进程（用于需要持续运行的命令）"""
    cmd = get_adb_command()
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(args)

    return await asyncio.create_subprocess_exec(
        *cmd,
        stdout=stdout,
        stderr=stderr,
    )
