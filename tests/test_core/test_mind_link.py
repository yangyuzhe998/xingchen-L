import pytest
import time
from src.psyche.services.mind_link import MindLink

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
    future_time = time.time() + 3960
    monkeypatch.setattr(time, "time", lambda: future_time)
    
    result = ml.read_intuition()
    assert result.startswith("(模糊的直觉)")
    assert "重要直觉" in result

def test_intuition_expire(temp_mind_link, monkeypatch):
    """验证直觉过期逻辑 (2h后)"""
    ml = temp_mind_link
    ml.inject_intuition("旧直觉", source="test")
    
    # 模拟 2.1 小时后 (7560s)
    future_time = time.time() + 7560
    monkeypatch.setattr(time, "time", lambda: future_time)
    
    result = ml.read_intuition()
    assert result == "保持观察，暂无强烈直觉。"

def test_empty_initial_state(temp_mind_link):
    """验证初始状态"""
    ml = temp_mind_link
    # 初始状态应返回默认值或空
    assert "保持警惕" in ml.read_intuition()
