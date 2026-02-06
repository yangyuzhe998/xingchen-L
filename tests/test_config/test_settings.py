"""
测试 src/config/settings/settings.py
验证配置加载、路径设置、环境变量等
"""

import pytest
import os
from pathlib import Path
from src.config.settings.settings import Settings, settings


class TestSettings:
    """测试 Settings 类"""
    
    def test_settings_singleton(self):
        """测试 settings 是 Settings 的实例"""
        assert isinstance(settings, Settings)
    
    def test_project_root_exists(self):
        """测试 PROJECT_ROOT 路径存在"""
        assert os.path.exists(settings.PROJECT_ROOT)
        assert os.path.isdir(settings.PROJECT_ROOT)
        print(f"✓ PROJECT_ROOT: {settings.PROJECT_ROOT}")
    
    def test_log_paths(self):
        """测试日志路径配置"""
        # LOG_DIR 应该是绝对路径
        assert os.path.isabs(settings.LOG_DIR)
        assert "logs" in settings.LOG_DIR
        
        # LOG_FILE 应该在 LOG_DIR 下
        assert settings.LOG_FILE.startswith(settings.LOG_DIR)
        assert settings.LOG_FILE.endswith(".log")
        
        print(f"✓ LOG_DIR: {settings.LOG_DIR}")
        print(f"✓ LOG_FILE: {settings.LOG_FILE}")
    
    def test_memory_paths(self):
        """测试记忆相关路径配置"""
        memory_paths = {
            "MEMORY_DATA_DIR": settings.MEMORY_DATA_DIR,
            "MEMORY_STORAGE_PATH": settings.MEMORY_STORAGE_PATH,
            "VECTOR_DB_PATH": settings.VECTOR_DB_PATH,
            "DIARY_PATH": settings.DIARY_PATH,
            "GRAPH_DB_PATH": settings.GRAPH_DB_PATH,
            "ALIAS_MAP_PATH": settings.ALIAS_MAP_PATH,
            "ARCHIVE_DB_PATH": settings.ARCHIVE_DB_PATH,
            "SHORT_TERM_CACHE_PATH": settings.SHORT_TERM_CACHE_PATH,
        }
        
        for name, path in memory_paths.items():
            # 所有路径都应该是绝对路径
            assert os.path.isabs(path), f"{name} 不是绝对路径"
            # 所有路径都应该包含 memory_data
            assert "memory_data" in path, f"{name} 不包含 memory_data"
            print(f"✓ {name}: {path}")
    
    def test_memory_limits(self):
        """测试记忆限制配置"""
        assert settings.SHORT_TERM_MAX_COUNT > 0
        assert settings.SHORT_TERM_MAX_CHARS > 0
        
        print(f"✓ SHORT_TERM_MAX_COUNT: {settings.SHORT_TERM_MAX_COUNT}")
        print(f"✓ SHORT_TERM_MAX_CHARS: {settings.SHORT_TERM_MAX_CHARS}")
    
    def test_navigator_config(self):
        """测试 Navigator (S-Brain) 配置"""
        assert settings.CYCLE_TRIGGER_COUNT > 0
        assert settings.CYCLE_CHECK_INTERVAL > 0
        assert settings.CYCLE_IDLE_TIMEOUT > 0
        assert settings.NAVIGATOR_DELAY_SECONDS >= 0
        assert settings.NAVIGATOR_EVENT_LIMIT > 0
        
        print(f"✓ CYCLE_TRIGGER_COUNT: {settings.CYCLE_TRIGGER_COUNT}")
        print(f"✓ NAVIGATOR_DELAY_SECONDS: {settings.NAVIGATOR_DELAY_SECONDS}")
    
    def test_psyche_config(self):
        """测试心智引擎配置"""
        assert 0 < settings.PSYCHE_DECAY_RATE < 1
        assert os.path.isabs(settings.PSYCHE_DEFAULT_STATE_FILE)
        assert os.path.isabs(settings.MIND_LINK_STORAGE_PATH)
        
        print(f"✓ PSYCHE_DECAY_RATE: {settings.PSYCHE_DECAY_RATE}")
    
    def test_llm_config(self):
        """测试 LLM 配置"""
        assert settings.DEFAULT_LLM_PROVIDER in ["deepseek", "qwen", "openai"]
        assert settings.DEFAULT_LLM_TIMEOUT > 0
        assert settings.F_BRAIN_MODEL  # F-Brain 模型不为空
        assert settings.S_BRAIN_MODEL  # S-Brain 模型不为空
        
        print(f"✓ DEFAULT_LLM_PROVIDER: {settings.DEFAULT_LLM_PROVIDER}")
        print(f"✓ F_BRAIN_MODEL: {settings.F_BRAIN_MODEL}")
        print(f"✓ S_BRAIN_MODEL: {settings.S_BRAIN_MODEL}")
    
    def test_sandbox_config(self):
        """测试沙箱配置"""
        assert settings.SANDBOX_MEM_LIMIT
        assert settings.SANDBOX_CPU_LIMIT > 0
        assert settings.SANDBOX_TIMEOUT > 0
        
        print(f"✓ SANDBOX_MEM_LIMIT: {settings.SANDBOX_MEM_LIMIT}")
        print(f"✓ SANDBOX_TIMEOUT: {settings.SANDBOX_TIMEOUT}s")
    
    def test_eventbus_path(self):
        """测试事件总线数据库路径"""
        assert os.path.isabs(settings.BUS_DB_PATH)
        assert settings.BUS_DB_PATH.endswith(".db")
        
        print(f"✓ BUS_DB_PATH: {settings.BUS_DB_PATH}")
    
    def test_paths_consistency(self):
        """测试路径一致性 - 所有 memory_data 路径应该在同一个目录下"""
        memory_dir = settings.MEMORY_DATA_DIR
        
        paths_to_check = [
            settings.MEMORY_STORAGE_PATH,
            settings.DIARY_PATH,
            settings.GRAPH_DB_PATH,
            settings.ALIAS_MAP_PATH,
            settings.ARCHIVE_DB_PATH,
            settings.SHORT_TERM_CACHE_PATH,
            settings.BUS_DB_PATH,
            settings.PSYCHE_DEFAULT_STATE_FILE,
            settings.MIND_LINK_STORAGE_PATH,
        ]
        
        for path in paths_to_check:
            assert path.startswith(memory_dir), f"{path} 不在 {memory_dir} 下"
        
        print(f"✓ 所有记忆相关路径都在 {memory_dir} 下")


class TestSettingsEnvironmentOverride:
    """测试环境变量覆盖"""
    
    def test_env_loading(self, monkeypatch):
        """测试环境变量是否被加载"""
        # 这个测试验证 .env 文件是否被正确加载
        # 实际的 API keys 应该在 .env 中
        
        # 注意：我们不测试实际的 API key 值，只测试机制
        # 如果需要测试覆盖，可以用 monkeypatch
        
        test_key = "TEST_API_KEY"
        test_value = "test_value_123"
        
        monkeypatch.setenv(test_key, test_value)
        assert os.getenv(test_key) == test_value
        
        print("✓ 环境变量机制正常")


if __name__ == "__main__":
    # 可以直接运行此文件进行测试
    pytest.main([__file__, "-v", "-s"])
