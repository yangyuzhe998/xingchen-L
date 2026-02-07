"""
测试 src/memory/services/memory_service.py
验证 MemoryService 核心功能：短期记忆、长期记忆、Cache 机制

注意：简化版测试，避免 ChromaDB 文件锁定问题
"""

import pytest
import os
from pathlib import Path
from src.memory.services.memory_service import MemoryService
from src.memory.storage.vector import ChromaStorage
from src.memory.storage.local import JsonStorage
from src.memory.storage.diary import DiaryStorage


@pytest.fixture
def memory_service(tmp_path):
    """创建测试用的 MemoryService 实例，使用隔离的临时目录"""
    from src.config.settings.settings import settings
    
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
        
        print(f"✓ 短期记忆添加成功，当前 {len(memory_service.short_term)} 条")
    
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
        
        print(f"✓ 获取最近历史成功，返回 {len(history)} 条")


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
        
        print(f"✓ 长期记忆添加成功，当前 {len(memory_service.long_term)} 条")
    
    def test_search_long_term(self, memory_service):
        """测试搜索长期记忆"""
        # 添加一些事实
        memory_service.add_long_term("用户喜欢 Python 编程", category="fact")
        memory_service.add_long_term("用户喜欢阅读技术书籍", category="fact")
        
        # 搜索 - get_relevant_long_term 返回字符串
        results = memory_service.get_relevant_long_term("编程", limit=5)
        
        # 验证
        assert isinstance(results, str)
        assert "编程" in results or "Python" in results
        
        print(f"✓ 长期记忆搜索成功")
    
    def test_commit_long_term(self, memory_service):
        """测试提交长期记忆到持久化存储"""
        # 添加数据
        memory_service.add_long_term("测试事实1", category="fact")
        memory_service.add_long_term("测试事实2", category="fact")
        
        # 提交
        memory_service.commit_long_term()
        
        # 验证文件存在
        assert os.path.exists(memory_service.json_storage.file_path)
        
        print(f"✓ 长期记忆提交成功")


class TestMemoryServiceCache:
    """测试 Cache 机制"""
    
    def test_save_cache(self, memory_service):
        """测试保存 Cache"""
        # 添加短期记忆
        memory_service.add_short_term("user", "缓存测试消息1")
        memory_service.add_short_term("assistant", "收到")
        
        # 保存 Cache
        memory_service.save_cache()
        
        # 验证 Cache 文件存在
        cache_path = "src/memory_data/short_term_cache.json"
        assert os.path.exists(cache_path)
        
        print(f"✓ Cache 保存成功")


class TestMemoryServiceDirtyFlags:
    """测试 Dirty Flag 机制"""
    
    def test_short_term_dirty_flag(self, memory_service):
        """测试短期记忆 dirty flag"""
        # 重置 dirty flag
        memory_service._short_term_dirty = False
        
        # 添加数据
        memory_service.add_short_term("user", "测试 dirty flag")
        
        # 验证 dirty flag 被设置
        assert memory_service._short_term_dirty == True
        
        # 保存后应该清除
        memory_service.save_cache()
        assert memory_service._short_term_dirty == False
        
        print(f"✓ 短期记忆 dirty flag 机制正常")
    
    def test_long_term_dirty_flag(self, memory_service):
        """测试长期记忆 dirty flag"""
        # 重置 dirty flag
        memory_service._long_term_dirty = False
        
        # 添加数据
        memory_service.add_long_term("测试 dirty flag", category="fact")
        
        # 验证 dirty flag 被设置
        assert memory_service._long_term_dirty == True
        
        # 提交后应该清除
        memory_service.commit_long_term()
        assert memory_service._long_term_dirty == False
        
        print(f"✓ 长期记忆 dirty flag 机制正常")


class TestMemoryServiceAlias:
    """测试别名功能"""
    
    def test_save_and_search_alias(self, memory_service):
        """测试保存和搜索别名"""
        # 保存别名
        memory_service.save_alias("仔仔", "User")
        
        # 搜索别名
        result = memory_service.search_alias("仔仔饿了")
        
        # 验证
        assert result is not None
        assert result[0] == "仔仔"
        assert result[1] == "User"
        
        print(f"✓ 别名保存和搜索成功")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
