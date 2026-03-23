"""
pytest 配置文件
提供测试夹具和全局配置
"""

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="function")
def clean_memory_data(tmp_path):
    """
    每个测试前清理测试专用的记忆数据
    使用 pytest 内置的 tmp_path 确保完全隔离
    """
    test_memory_dir = tmp_path / "memory_data"
    test_memory_dir.mkdir(parents=True, exist_ok=True)

    yield test_memory_dir


@pytest.fixture(scope="function")
def clean_wal(tmp_path):
    """
    提供隔离的 WAL 实例，使用临时目录避免数据污染
    """
    from xingchen.memory.wal import WriteAheadLog

    wal_path = tmp_path / "wal.log"
    wal = WriteAheadLog(log_path=str(wal_path))

    yield wal


@pytest.fixture(scope="session")
def test_api_keys():
    """
    测试用的 API Keys
    从环境变量读取
    """
    return {
        "qwen": os.getenv("DASHSCOPE_API_KEY"),
        "deepseek": os.getenv("DEEPSEEK_API_KEY"),
    }


@pytest.fixture
def sample_conversations():
    """
    示例对话数据
    用于测试记忆和对话功能
    """
    return [
        ("user", "你好，我叫张三"),
        ("assistant", "你好张三！很高兴认识你。"),
        ("user", "我喜欢编程"),
        ("assistant", "编程是一个很有趣的爱好！你喜欢哪种编程语言？"),
        ("user", "我喜欢 Python"),
        ("assistant", "Python 是一门很棒的语言！简洁而强大。"),
    ]


@pytest.fixture
def sample_facts():
    """
    示例事实数据
    用于测试长期记忆
    """
    return [
        "用户名叫张三",
        "用户喜欢编程",
        "用户喜欢 Python 语言",
        "用户的生日是 1990-01-01",
        "用户住在北京",
    ]


@pytest.fixture(scope="function")
def isolated_event_bus(monkeypatch, tmp_path):
    """为测试提供隔离的全局 event_bus（避免写入真实 bus.db、避免订阅者泄漏）。"""
    from xingchen.core.event_bus import SQLiteEventBus

    db_path = tmp_path / "test_bus.db"
    bus = SQLiteEventBus(db_path=str(db_path))

    monkeypatch.setattr("xingchen.core.event_bus.event_bus", bus)
    return bus


@pytest.fixture(scope="function")
def isolated_psyche_engine(monkeypatch, tmp_path):
    """为测试提供隔离的全局 psyche_engine（避免污染 psyche_state.json）。"""
    from xingchen.psyche.engine import PsycheEngine

    state_path = tmp_path / "psyche_state_test.json"
    engine = PsycheEngine(state_file_path=str(state_path))

    monkeypatch.setattr("xingchen.psyche.psyche_engine", engine)
    return engine
