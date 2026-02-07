import pytest
import os
import sqlite3
import time
import threading
from pathlib import Path
from src.core.bus.event_bus import SQLiteEventBus
from src.schemas.events import BaseEvent as Event, EventType


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
        
        print(f"✓ EventBus 初始化成功")
    
    def test_eventbus_database_schema(self, clean_event_bus):
        """测试数据库表结构"""
        bus = clean_event_bus
        
        # 查询表结构
        with sqlite3.connect(bus.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
        
        assert "events" in tables
        
        print(f"✓ 数据库表结构正确")
    
    def test_eventbus_has_indexes(self, clean_event_bus):
        """测试索引创建"""
        bus = clean_event_bus
        
        with sqlite3.connect(bus.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
        
        assert any("timestamp" in idx for idx in indexes)
        assert any("type" in idx for idx in indexes)
        
        print(f"✓ 数据库索引已创建")


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
        
        print(f"✓ 事件发布成功，ID: {event_id}")
    
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
        
        print(f"✓ 批量发布成功，{len(event_ids)} 个事件")
    
    def test_publish_with_chinese(self, clean_event_bus):
        """测试发布包含中文的事件"""
        bus = clean_event_bus
        
        event = Event(
            type=EventType.SYSTEM_NOTIFICATION,
            source="测试源",
            payload={"消息": "你好世界"},
            meta={"标签": "测试"}
        )
        
        event_id = bus.publish(event)
        assert event_id > 0
        
        # 验证可以读取 - 使用 get_latest_cycle 获取最近的事件
        events = bus.get_latest_cycle(limit=10)
        assert len(events) > 0
        
        # 找到刚刚发布的事件
        published_event = next((e for e in events if e.id == event_id), None)
        assert published_event is not None, f"未找到 event_id={event_id} 的事件"
        
        # 使用 payload_data 属性安全访问字典
        payload_dict = published_event.payload_data
        assert payload_dict["消息"] == "你好世界"
        assert published_event.source == "测试源"
        
        print(f"✓ 中文事件发布成功")


class TestEventBusSubscribe:
    """测试事件订阅"""
    
    def test_subscribe_callback(self, clean_event_bus):
        """测试订阅回调"""
        bus = clean_event_bus
        
        received_events = []
        
        def callback(event):
            received_events.append(event)
        
        bus.subscribe(callback)
        
        # 发布事件
        event = Event(
            type=EventType.SYSTEM_NOTIFICATION,
            source="test",
            payload={"data": "test"},
            meta={}
        )
        bus.publish(event)
        
        # 等待异步通知
        time.sleep(0.1)
        
        assert len(received_events) > 0
        assert received_events[0].type == EventType.SYSTEM_NOTIFICATION.value
        
        print(f"✓ 订阅回调成功")
    
    def test_multiple_subscribers(self, clean_event_bus):
        """测试多个订阅者"""
        bus = clean_event_bus
        
        received1 = []
        received2 = []
        
        bus.subscribe(lambda e: received1.append(e))
        bus.subscribe(lambda e: received2.append(e))
        
        event = Event(
            type=EventType.SYSTEM_NOTIFICATION,
            source="test",
            payload={},
            meta={}
        )
        bus.publish(event)
        
        time.sleep(0.1)
        
        assert len(received1) > 0
        assert len(received2) > 0
        
        print(f"✓ 多订阅者通知成功")


class TestEventBusQuery:
    """测试事件查询"""
    
    def test_get_events(self, clean_event_bus):
        """测试获取事件"""
        bus = clean_event_bus
        
        # 发布几个事件
        for i in range(3):
            event = Event(
                type=EventType.SYSTEM_NOTIFICATION,
                source="test",
                payload={"index": i},
                meta={}
            )
            bus.publish(event)
        
        # 查询
        events = bus.get_events(limit=10)
        
        assert len(events) >= 3
        
        print(f"✓ 事件查询成功，获取 {len(events)} 条")
    
    def test_get_events_by_type(self, clean_event_bus):
        """测试按类型查询"""
        bus = clean_event_bus
        
        # 发布不同类型
        bus.publish(Event(type=EventType.USER_INPUT, source="test", payload={}, meta={}))
        bus.publish(Event(type=EventType.DRIVER_RESPONSE, source="test", payload={}, meta={}))
        bus.publish(Event(type=EventType.USER_INPUT, source="test", payload={}, meta={}))
        
        # 查询 USER_INPUT
        events = bus.get_events(event_type=EventType.USER_INPUT)
        
        assert len(events) == 2
        assert all(e.type == EventType.USER_INPUT.value for e in events)
        
        print(f"✓ 按类型查询成功")
    
    def test_get_latest_cycle(self, clean_event_bus):
        """测试获取最近周期"""
        bus = clean_event_bus
        
        # 发布一些事件
        for i in range(5):
            event = Event(
                type=EventType.SYSTEM_NOTIFICATION,
                source="test",
                payload={"index": i},
                meta={}
            )
            bus.publish(event)
        
        # 获取最近周期
        events = bus.get_latest_cycle(limit=3)
        
        assert len(events) <= 3
        # 验证顺序（应该是时间正序）
        if len(events) > 1:
            assert events[0].timestamp <= events[-1].timestamp
        
        print(f"✓ 获取最近周期成功")


class TestEventBusThreadSafety:
    """测试线程安全"""
    
    def test_concurrent_publish(self, clean_event_bus):
        """测试并发发布"""
        bus = clean_event_bus
        
        def publish_events(count):
            for i in range(count):
                event = Event(
                    type=EventType.SYSTEM_NOTIFICATION,
                    source="test",
                    payload={"thread": threading.current_thread().name},
                    meta={}
                )
                bus.publish(event)
        
        # 创建多个线程
        threads = []
        for i in range(3):
            t = threading.Thread(target=publish_events, args=(5,))
            threads.append(t)
            t.start()
        
        # 等待完成
        for t in threads:
            t.join()
        
        # 验证所有事件都被发布
        events = bus.get_events(event_type=EventType.SYSTEM_NOTIFICATION, limit=100)
        assert len(events) == 15  # 3 threads * 5 events
        
        print(f"✓ 并发发布测试通过")


class TestEventBusGlobalInstance:
    """测试全局实例"""
    
    def test_global_event_bus_exists(self):
        """测试全局 event_bus 存在"""
        from src.core.bus.event_bus import event_bus
        
        assert event_bus is not None
        assert isinstance(event_bus, SQLiteEventBus)
        
        print(f"✓ 全局 event_bus 实例存在")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])



