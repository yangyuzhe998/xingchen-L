import sqlite3
import json
import uuid
import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime
import threading
from config.settings import settings

@dataclass
class Event:
    type: str  # e.g., "user_input", "driver_response", "navigator_suggestion"
    source: str # e.g., "user", "driver", "navigator"
    payload: Dict[str, Any] # 主要内容
    meta: Dict[str, Any] # "暗物质"信息：trace_id, internal_thoughts, emotion, psyche_state
    trace_id: str = ""
    timestamp: float = 0.0
    id: Optional[int] = None

    def __post_init__(self):
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = time.time()

class SQLiteEventBus:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path else settings.BUS_DB_PATH
        self._init_db()
        self._lock = threading.Lock() # 简单的线程锁，防止并发写入冲突

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
        print(f"[EventBus] 总线已连接: {self.db_path}")

    def publish(self, event: Event) -> int:
        """发布事件"""
        with self._lock:
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
                    json.dumps(event.payload, ensure_ascii=False),
                    json.dumps(event.meta, ensure_ascii=False)
                ))
                event_id = cursor.lastrowid
                conn.commit()
                # print(f"[Bus] Event Published: [{event.type}] from {event.source} (ID: {event_id})")
                return event_id

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
