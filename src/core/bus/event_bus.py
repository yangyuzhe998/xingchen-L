import sqlite3
import json
import uuid
import time
import os
import atexit
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime
import threading
from src.config.settings.settings import settings
from src.utils.logger import logger
from src.schemas.events import BaseEvent as Event  # 引入 Pydantic Event


class SQLiteEventBus:
    def __init__(self, db_path=None, max_workers=10):
        self.db_path = db_path if db_path else settings.BUS_DB_PATH
        self._init_db()
        self._lock = threading.Lock()  # 简单的线程锁，防止并发写入冲突
        self._subscribers = []  # 观察者列表

        # 线程池：用于异步通知订阅者，避免每事件一线程导致的线程爆炸
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="EventBus")

        # 确保程序退出时优雅关闭线程池
        atexit.register(self.shutdown)

    def subscribe(self, callback):
        """订阅事件"""
        self._subscribers.append(callback)

    def shutdown(self):
        """关闭线程池 (程序退出时调用)"""
        if hasattr(self, "_executor") and self._executor:
            self._executor.shutdown(wait=False)
            logger.debug("[EventBus] ThreadPool shutdown.")

    def _init_db(self):
        """初始化数据库表结构"""
        # 确保父目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    meta TEXT NOT NULL
                )
            """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON events (timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON events (type)")
            conn.commit()
        logger.info(f"[EventBus] 总线已连接: {self.db_path}")

    def publish(self, event: Event) -> int:
        """发布事件"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO events (trace_id, timestamp, type, source, payload, meta)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        event.trace_id,
                        event.timestamp,
                        event.type,
                        event.source,
                        json.dumps(
                            event.payload if isinstance(event.payload, dict) else event.payload.model_dump(),
                            ensure_ascii=False,
                        ),
                        json.dumps(event.meta, ensure_ascii=False),
                    ),
                )
                event_id = cursor.lastrowid
                conn.commit()

                event.id = event_id

        self._notify_subscribers(event)

        return event_id

    def _notify_subscribers(self, event):
        """通知订阅者 (使用线程池)"""
        for callback in self._subscribers:
            try:
                self._executor.submit(self._safe_callback, callback, event)
            except Exception as e:
                logger.error(f"[Bus] Failed to submit callback: {e}", exc_info=True)

    def _safe_callback(self, callback, event):
        """安全执行回调 (捕获异常)"""
        try:
            callback(event)
        except Exception as e:
            logger.error(f"[Bus] Subscriber callback error: {e}", exc_info=True)

    def get_events(self, limit=20, offset=0, event_type=None, start_time=None) -> List[Event]:
        """查询事件历史"""
        query = "SELECT id, trace_id, timestamp, type, source, payload, meta FROM events"
        params = []
        conditions = []

        if event_type:
            conditions.append("type = ?")
            params.append(event_type)
        if start_time:
            conditions.append("timestamp > ?")
            params.append(start_time)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        events = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                events.append(
                    Event(
                        id=row[0],
                        trace_id=row[1],
                        timestamp=row[2],
                        type=row[3],
                        source=row[4],
                        payload=json.loads(row[5]),
                        meta=json.loads(row[6]),
                    )
                )
        return events

    def get_latest_cycle(self, limit=50) -> List[Event]:
        """获取最近的一个周期（用于 S脑分析）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, trace_id, timestamp, type, source, payload, meta
                FROM events
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (limit,),
            )
            rows = cursor.fetchall()

        events = []
        for row in reversed(rows):
            events.append(
                Event(
                    id=row[0],
                    trace_id=row[1],
                    timestamp=row[2],
                    type=row[3],
                    source=row[4],
                    payload=json.loads(row[5]),
                    meta=json.loads(row[6]),
                )
            )
        return events

    def cleanup_old_events(self, days: int = 30) -> int:
        """清理过期事件 (Production Hardening)"""
        cutoff_timestamp = time.time() - (days * 86400)
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_timestamp,))
                    count = cursor.rowcount
                    conn.commit()
            return count
        except Exception as e:
            logger.error(f"[Bus] Cleanup failed: {e}")
            return 0


_event_bus_instance: Optional[SQLiteEventBus] = None


def get_event_bus() -> SQLiteEventBus:
    """获取全局 EventBus 实例（延迟初始化）。"""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = SQLiteEventBus()
    return _event_bus_instance


class _EventBusProxy(SQLiteEventBus):
    """
    延迟初始化代理类。
    继承自 SQLiteEventBus 以通过 isinstance 检查。
    """

    def __init__(self):
        # 覆盖父类 __init__，防止在 import 时触发初始化
        pass

    def __getattribute__(self, name):
        # 拦截方法和属性访问，确保返回真实实例的属性
        if name in ("__class__", "__instancecheck__", "__subclasscheck__"):
            return super().__getattribute__(name)
        return getattr(get_event_bus(), name)


# 全局代理（保持原 import 使用方式不变）
event_bus = _EventBusProxy()
