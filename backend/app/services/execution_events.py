"""执行事件发布-订阅系统"""

import asyncio
from typing import Any
from collections import defaultdict


class ExecutionEventBus:
    """执行事件总线 - 用于实时推送执行步骤"""

    _instance: "ExecutionEventBus | None" = None

    def __init__(self):
        # execution_id -> list of asyncio.Queue
        self._subscribers: dict[int, list[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "ExecutionEventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def subscribe(self, execution_id: int) -> asyncio.Queue:
        """订阅执行事件，返回一个队列用于接收事件"""
        q: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subscribers[execution_id].append(q)
        return q

    async def unsubscribe(self, execution_id: int, q: asyncio.Queue):
        """取消订阅"""
        async with self._lock:
            if execution_id in self._subscribers:
                try:
                    self._subscribers[execution_id].remove(q)
                except ValueError:
                    pass
                if not self._subscribers[execution_id]:
                    del self._subscribers[execution_id]

    async def publish(self, execution_id: int, event_type: str, data: Any):
        """发布事件到所有订阅者"""
        async with self._lock:
            subscribers = self._subscribers.get(execution_id, [])
            for q in subscribers:
                try:
                    q.put_nowait({"type": event_type, "data": data})
                except asyncio.QueueFull:
                    pass  # 跳过满的队列

    def publish_sync(self, execution_id: int, event_type: str, data: Any):
        """同步版本的发布（从线程中调用）"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.publish(execution_id, event_type, data),
                    loop
                )
        except RuntimeError:
            pass  # 没有事件循环时忽略


# 全局事件总线实例
event_bus = ExecutionEventBus.get_instance()
