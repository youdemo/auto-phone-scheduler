"""
基于 scrcpy 的低延迟设备屏幕流服务
使用 scrcpy + ffmpeg 输出 MJPEG 流
"""
import asyncio
import logging
from typing import AsyncGenerator

from app.services.adb import run_adb

logger = logging.getLogger(__name__)


class DeviceStreamer:
    """设备屏幕流管理器"""

    def __init__(self):
        self._streams: dict[str, asyncio.subprocess.Process] = {}
        self._lock = asyncio.Lock()

    async def start_stream(self, device_serial: str) -> asyncio.subprocess.Process | None:
        """启动设备的 scrcpy 流"""
        async with self._lock:
            # 如果已有流在运行，直接返回
            if device_serial in self._streams:
                proc = self._streams[device_serial]
                if proc.returncode is None:
                    return proc
                # 进程已结束，清理
                del self._streams[device_serial]

            try:
                # 使用 scrcpy 输出原始视频流到 stdout，然后用 ffmpeg 转成 MJPEG
                # scrcpy 参数：
                #   --no-playback: 不显示窗口
                #   --video-codec=h264: 使用 h264 编码
                #   --max-size=720: 限制最大尺寸
                #   --max-fps=15: 限制帧率降低带宽
                #   --video-bit-rate=2M: 限制码率
                #   -s: 指定设备
                # 通过管道传给 ffmpeg 转成 MJPEG
                cmd = (
                    f"scrcpy --serial={device_serial} --no-playback --no-audio "
                    f"--video-codec=h264 --max-size=720 --max-fps=15 "
                    f"--video-bit-rate=2M --render-driver=software "
                    f"--v4l2-sink=/dev/null --record=- --record-format=mp4 2>/dev/null | "
                    f"ffmpeg -i pipe:0 -f mjpeg -q:v 5 -r 10 pipe:1 2>/dev/null"
                )

                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )

                self._streams[device_serial] = proc
                logger.info(f"Started stream for device {device_serial}")
                return proc

            except Exception as e:
                logger.error(f"Failed to start stream for {device_serial}: {e}")
                return None

    async def stop_stream(self, device_serial: str):
        """停止设备的流"""
        async with self._lock:
            if device_serial in self._streams:
                proc = self._streams[device_serial]
                if proc.returncode is None:
                    proc.terminate()
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        proc.kill()
                del self._streams[device_serial]
                logger.info(f"Stopped stream for device {device_serial}")

    async def stop_all(self):
        """停止所有流"""
        for serial in list(self._streams.keys()):
            await self.stop_stream(serial)


# 全局实例
_streamer: DeviceStreamer | None = None


def get_streamer() -> DeviceStreamer:
    global _streamer
    if _streamer is None:
        _streamer = DeviceStreamer()
    return _streamer


async def generate_mjpeg_stream(device_serial: str) -> AsyncGenerator[bytes, None]:
    """生成 MJPEG 流的异步生成器（使用 adb 截图）"""
    while True:
        try:
            # 使用 adb 截图方式
            stdout, _ = await run_adb("exec-out", "screencap", "-p", serial=device_serial)

            if stdout and len(stdout) > 100:
                # 构造 multipart 帧（浏览器可以直接显示 PNG）
                yield b"--frame\r\n"
                yield b"Content-Type: image/png\r\n"
                yield f"Content-Length: {len(stdout)}\r\n\r\n".encode()
                yield stdout
                yield b"\r\n"

            # 控制帧率（约 5 fps）
            await asyncio.sleep(0.2)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Stream error for {device_serial}: {e}")
            await asyncio.sleep(1)

