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
    from src.memory.storage.write_ahead_log import WriteAheadLog

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
    from src.core.bus.event_bus import SQLiteEventBus

    db_path = tmp_path / "test_bus.db"
    bus = SQLiteEventBus(db_path=str(db_path))

    monkeypatch.setattr("src.core.bus.event_bus.event_bus", bus)
    return bus


@pytest.fixture(scope="function")
def isolated_psyche_engine(monkeypatch, tmp_path):
    """为测试提供隔离的全局 psyche_engine（避免污染 psyche_state.json）。"""
    from src.psyche.core.engine import PsycheEngine

    state_path = tmp_path / "psyche_state_test.json"
    engine = PsycheEngine(state_file_path=str(state_path))

    monkeypatch.setattr("src.psyche.psyche_engine", engine)
    return engine


@pytest.fixture(scope="function")
def isolated_mind_link(monkeypatch, tmp_path):
    """为测试提供隔离的全局 mind_link（避免污染 mind_link_buffer.json）。"""
    from src.psyche.services.mind_link import MindLink

    storage_path = tmp_path / "mind_link_test.json"
    ml = MindLink(storage_path=str(storage_path))

    monkeypatch.setattr("src.psyche.mind_link", ml)
    return ml


def pytest_configure(config):
    """pytest 启动时的配置"""
    config.addinivalue_line("markers", "slow: 标记慢速测试（需要 LLM API 调用）")
    config.addinivalue_line("markers", "integration: 标记集成测试")
    config.addinivalue_line("markers", "stress: 标记压力测试")


def pytest_collection_modifyitems(config, items):
    """修改测试收集行为"""
    skip_slow = pytest.mark.skip(reason="需要 --runslow 选项来运行")

    for item in items:
        if "slow" in item.keywords and not config.getoption("--runslow", default=False):
            item.add_marker(skip_slow)


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="运行慢速测试（包括 LLM API 调用）",
    )
