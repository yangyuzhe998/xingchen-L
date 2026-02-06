import sqlite3
import json
import uuid
import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime
import threading
from ...config.settings.settings import settings
from ...utils.logger import logger
from ...schemas.events import BaseEvent as Event # 引入 Pydantic Event

class SQLiteEventBus:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path else settings.BUS_DB_PATH
        self._init_db()
        self._lock = threading.Lock() # 简单的线程锁，防止并发写入冲突
        self._subscribers = [] # 观察者列表

    def subscribe(self, callback):
        """订阅事件"""
        self._subscribers.append(callback)

    def _init_db(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 创建 events 表
            # meta 和 payload 存储为 JSON 字符串
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    meta TEXT NOT NULL
                )
            ''')
            # 创建索引以加速查询
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON events (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON events (type)')
            conn.commit()
        logger.info(f"[EventBus] 总线已连接: {self.db_path}")

    def publish(self, event: Event) -> int:
        """发布事件"""
        # 使用 Context Manager 模式自动处理连接和事务
        # 如果发生异常，外层调用者应该知道（或者在这里降级处理，但不应静默吞掉关键错误）
        # 鉴于 EventBus 是核心组件，我们保持 fail-fast 或显式报错的风格
        
        with self._lock:
            # 直接执行数据库操作，如果出错，让异常向上传播
            # 调用者需要处理 sqlite3.Error
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO events (trace_id, timestamp, type, source, payload, meta)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    event.trace_id,
                    event.timestamp,
                    event.type,
                    event.source,
                    json.dumps(event.payload if isinstance(event.payload, dict) else event.payload.model_dump(), ensure_ascii=False),
                    json.dumps(event.meta, ensure_ascii=False)
                ))
                event_id = cursor.lastrowid
                conn.commit()
                
                # 为新插入的事件设置 ID
                event.id = event_id

        # 通知订阅者 (放在锁外或锁内？放在锁内保证顺序，放在锁外减少锁持有时间)
        # 这里选择放在锁内以简化逻辑，且 notify 是异步的 (start thread) 只有微小开销
        self._notify_subscribers(event)
        
        return event_id

    def _notify_subscribers(self, event):
        """通知订阅者"""
        for callback in self._subscribers:
            try:
                # [TODO] [FutureOptimization]: 当前使用每事件一线程的简单模式。
                # 如果并发量过高 (>100 QPS)，应升级为 ThreadPoolExecutor 以防止线程爆炸。
                # 目前保持简单，暂不引入线程池。
                threading.Thread(target=callback, args=(event,), daemon=True).start()
            except Exception as e:
                logger.error(f"[Bus] Subscriber Notification Failed: {e}", exc_info=True)

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

        query += " ORDER BY timestamp ASC LIMIT ? OFFSET ?" # 按时间正序排列
        params.extend([limit, offset])

        events = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                events.append(Event(
                    id=row[0],
                    trace_id=row[1],
                    timestamp=row[2],
                    type=row[3],
                    source=row[4],
                    payload=json.loads(row[5]),
                    meta=json.loads(row[6])
                ))
        return events

    def get_latest_cycle(self, limit=50) -> List[Event]:
        """获取最近的一个周期（用于 S脑分析）"""
        # 这里简单取最近 N 条，未来可以配合 CycleManager 做更复杂的逻辑
        # 注意：这里返回的是按时间倒序取出的，再转回正序
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, trace_id, timestamp, type, source, payload, meta 
                FROM events 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
        
        events = []
        for row in reversed(rows): # 转回正序
             events.append(Event(
                id=row[0],
                trace_id=row[1],
                timestamp=row[2],
                type=row[3],
                source=row[4],
                payload=json.loads(row[5]),
                meta=json.loads(row[6])
            ))
        return events

# 全局单例
event_bus = SQLiteEventBus()
