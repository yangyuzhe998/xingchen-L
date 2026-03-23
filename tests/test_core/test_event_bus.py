import pytest
import os
import sqlite3
import time
import threading
from pathlib import Path
from xingchen.core.event_bus import SQLiteEventBus
from xingchen.schemas.events import BaseEvent as Event, EventType


@pytest.fixture
def clean_event_bus(tmp_path):
    """创建干净的测试用 EventBus"""
    db_path = tmp_path / "test_events.db"
    bus = SQLiteEventBus(db_path=str(db_path))
    return bus


class TestEventBusInitialization:
    """测试 EventBus 初始化"""
    
    def test_eventbus_init(self, clean_event_bus):
        """测试 EventBus 初始化"""
        bus = clean_event_bus
        
        assert bus is not None
        assert os.path.exists(bus.db_path)
        
        print(f"✅ EventBus 初始化成功")
    
    def test_eventbus_database_schema(self, clean_event_bus):
        """测试数据库表结构"""
        bus = clean_event_bus
        
        # 查询表结构
        with sqlite3.connect(bus.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
        
        assert "events" in tables
        
        print(f"✅ 数据库表结构正确")
    
    def test_eventbus_has_indexes(self, clean_event_bus):
        """测试索引创建"""
        bus = clean_event_bus
        
        with sqlite3.connect(bus.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
        
        assert any("timestamp" in idx for idx in indexes)
        assert any("type" in idx for idx in indexes)
        
        print(f"✅ 数据库索引已创建")


class TestEventBusPublish:
    """测试事件发布"""
    
    def test_publish_event(self, clean_event_bus):
        """测试发布单个事件"""
        bus = clean_event_bus
        
        event = Event(
            type=EventType.SYSTEM_NOTIFICATION,
            source="test",
            payload={"message": "测试消息"},
            meta={}
        )
        
        event_id = bus.publish(event)
        
        assert event_id is not None
        assert event_id > 0
        assert event.id == event_id
        
        print(f"✅ 事件发布成功，ID: {event_id}")
    
    def test_publish_multiple_events(self, clean_event_bus):
        """测试发布多个事件"""
        bus = clean_event_bus
        
        event_ids = []
        for i in range(5):
            event = Event(
                type=EventType.SYSTEM_NOTIFICATION,
                source="test",
                payload={"index": i},
                meta={}
            )
            event_id = bus.publish(event)
            event_ids.append(event_id)
        
        assert len(event_ids) == 5
        assert len(set(event_ids)) == 5  # 所有 ID 唯一
        
        print(f"✅ 批量发布成功，{len(event_ids)} 个事件")
