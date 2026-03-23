import pytest
import time
from xingchen.psyche.mind_link import MindLink

@pytest.fixture
def temp_mind_link(tmp_path):
    """创建临时 MindLink 实例"""
    storage_path = tmp_path / "test_mind_link.json"
    return MindLink(storage_path=str(storage_path))

def test_inject_and_read(temp_mind_link):
    """验证直觉注入后能被正确读取"""
    ml = temp_mind_link
    ml.inject_intuition("测试直觉", source="test")
    assert ml.read_intuition() == "测试直觉"

def test_intuition_weaken(temp_mind_link, monkeypatch):
    """验证直觉弱化逻辑 (1h后)"""
    ml = temp_mind_link
    # 注入直觉
    ml.inject_intuition("重要直觉", source="test")
    
    # 模拟 1.1 小时后 (3960s)
    current_time = time.time()
    future_time = current_time + 3960
    monkeypatch.setattr(time, "time", lambda: future_time)
    
    result = ml.read_intuition()
    assert "重要直觉" in result
    assert "模糊" in result or "..." in result

def test_intuition_expire(temp_mind_link, monkeypatch):
    """验证直觉过期逻辑 (2h后)"""
    ml = temp_mind_link
    ml.inject_intuition("旧直觉", source="test")
    
    # 模拟 2.1 小时后 (7560s)
    current_time = time.time()
    future_time = current_time + 7560
    monkeypatch.setattr(time, "time", lambda: future_time)
    
    result = ml.read_intuition()
    # 过期后应返回默认直觉
    assert "保持" in result or "观察" in result

def test_empty_initial_state(temp_mind_link):
    """验证初始状态"""
    ml = temp_mind_link
    # 初始状态应返回默认值
    assert ml.read_intuition() is not None
    assert len(ml.read_intuition()) > 0
