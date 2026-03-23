"""
测试 xingchen/memory/service.py
验证 MemoryService 核心功能：短期记忆、长期记忆、Cache 机制

注意：简化版测试，避免 ChromaDB 文件锁定问题
"""

import pytest
import os
from pathlib import Path
from xingchen.memory.service import MemoryService
from xingchen.memory.storage.vector import ChromaStorage
from xingchen.memory.storage.local import JsonStorage
from xingchen.memory.storage.diary import DiaryStorage


@pytest.fixture
def memory_service(tmp_path):
    """创建测试用的 MemoryService 实例，使用隔离的临时目录"""
    from xingchen.config.settings import settings
    
    # 清空全局缓存路径（MemoryService 内部使用 settings 路径）
    # 这是一个 workaround，因为 MemoryService 混用了传入存储和全局 settings 路径
    global_cache_path = settings.SHORT_TERM_CACHE_PATH
    if os.path.exists(global_cache_path):
        try:
            os.remove(global_cache_path)
        except:
            pass
    
    test_dir = tmp_path / "memory_data"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    vector_storage = ChromaStorage(str(test_dir / "test_chroma"))
    json_storage = JsonStorage(str(test_dir / "test_long_term.json"))
    diary_storage = DiaryStorage(str(test_dir / "test_diary.md"))
    
    service = MemoryService(vector_storage, json_storage, diary_storage)
    return service


class TestMemoryServiceShortTerm:
    """测试短期记忆功能"""
    
    def test_add_short_term(self, memory_service):
        """测试添加短期记忆"""
        initial_count = len(memory_service.short_term)
        
        # 添加对话
        memory_service.add_short_term("user", "你好，我叫张三")
        memory_service.add_short_term("assistant", "你好张三！很高兴认识你。")
        
        # 验证
        assert len(memory_service.short_term) == initial_count + 2
        assert memory_service.short_term[-2].role == "user"
        assert memory_service.short_term[-2].content == "你好，我叫张三"
        assert memory_service.short_term[-1].role == "assistant"
        
        print(f"✅ 短期记忆添加成功，当前 {len(memory_service.short_term)} 条")
    
    def test_get_recent_history(self, memory_service):
        """测试获取最近历史"""
        # 添加一些对话
        memory_service.add_short_term("user", "测试历史1")
        memory_service.add_short_term("assistant", "回复1")
        
        # 获取最近历史
        history = memory_service.get_recent_history(limit=5)
        
        assert isinstance(history, list)
        assert len(history) > 0
        assert all(isinstance(item, dict) for item in history)
        
        print(f"✅ 获取最近历史成功，返回 {len(history)} 条")


class TestMemoryServiceLongTerm:
    """测试长期记忆功能"""
    
    def test_add_long_term(self, memory_service):
        """测试添加长期记忆"""
        initial_count = len(memory_service.long_term)
        
        # 添加事实
        memory_service.add_long_term("用户喜欢编程", category="fact")
        memory_service.add_long_term("用户住在北京", category="fact")
        
        # 验证
        assert len(memory_service.long_term) >= initial_count + 2
        
        # 检查是否包含添加的内容
        contents = [item.content for item in memory_service.long_term]
        assert "用户喜欢编程" in contents
        assert "用户住在北京" in contents
        
        print(f"✅ 长期记忆添加成功，当前 {len(memory_service.long_term)} 条")
    
    def test_search_long_term(self, memory_service):
        """测试搜索长期记忆"""
        # 添加一些事实
        memory_service.add_long_term("测试搜索1: 苹果是甜的", category="fact")
        memory_service.add_long_term("测试搜索2: 编程很有趣", category="fact")
        
        # 搜索
        results = memory_service.search_long_term("苹果")
        assert len(results) > 0
        assert any("苹果" in item.content for item in results)
        
        print(f"✅ 长期记忆搜索成功，返回 {len(results)} 条结果")
