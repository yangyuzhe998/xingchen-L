"""
pytest 配置文件
提供测试夹具和全局配置
"""

import pytest
import os
import shutil
from pathlib import Path


@pytest.fixture(scope="function")
def clean_memory_data(tmp_path):
    """
    每个测试前清理测试专用的记忆数据
    使用 pytest 内置的 tmp_path 确保完全隔离
    """
    test_memory_dir = tmp_path / "memory_data"
    test_memory_dir.mkdir(parents=True, exist_ok=True)
    
    yield test_memory_dir
    
    # tmp_path 会被 pytest 自动清理，无需手动清理


@pytest.fixture(scope="function")
def clean_wal(tmp_path):
    """
    提供隔离的 WAL 实例，使用临时目录避免数据污染
    """
    from src.memory.storage.write_ahead_log import WriteAheadLog
    
    wal_path = tmp_path / "wal.log"
    wal = WriteAheadLog(log_path=str(wal_path))
    
    yield wal
    
    # tmp_path 会被 pytest 自动清理


@pytest.fixture(scope="session")
def test_api_keys():
    """
    测试用的 API Keys
    从环境变量读取
    """
    return {
        "qwen": os.getenv("DASHSCOPE_API_KEY"),
        "deepseek": os.getenv("DEEPSEEK_API_KEY")
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


def pytest_configure(config):
    """pytest 启动时的配置"""
    # 设置测试标记
    config.addinivalue_line(
        "markers", "slow: 标记慢速测试（需要 LLM API 调用）"
    )
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )
    config.addinivalue_line(
        "markers", "stress: 标记压力测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集行为"""
    # 可以在这里添加自动跳过逻辑
    # 例如：如果没有 API key，跳过需要 API 的测试
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
        help="运行慢速测试（包括 LLM API 调用）"
    )
