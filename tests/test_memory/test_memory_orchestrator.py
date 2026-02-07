"""
测试 Memory Orchestrator
"""
import pytest
from unittest.mock import Mock, patch
from src.memory.services.memory_orchestrator import MemoryOrchestrator

class TestMemoryOrchestrator:
    
    @pytest.fixture
    def orchestrator(self):
        # 获取单例
        orch = MemoryOrchestrator()
        
        # 备份依赖
        original_ac = getattr(orch, 'auto_classifier', None)
        original_tm = getattr(orch, 'topic_manager', None)
        original_pending = getattr(orch, 'pending_path', None)
        
        # 注入 Mock
        orch.auto_classifier = Mock()
        orch.topic_manager = Mock()
        
        yield orch
        
        # 还原依赖
        if original_ac: orch.auto_classifier = original_ac
        if original_tm: orch.topic_manager = original_tm
        if original_pending: orch.pending_path = original_pending

    def test_classify_compressed_memory_success(self, orchestrator):
        """测试分类成功"""
        # 构造足够长的脚本以通过长度检查 (>50 chars)
        script = "User: Hello there! I am testing the memory system.\nAI: Hi! How can I help you today? This is a long enough script."
        
        # 直接 Mock 实例属性
        orchestrator.auto_classifier.classify_and_store.return_value = "frag_123"
        
        result = orchestrator.classify_compressed_memory(script)
        
        assert result["success"] == 1
        assert result["fragment_id"] == "frag_123"
        orchestrator.auto_classifier.classify_and_store.assert_called_once()
        
        assert result["success"] == 1
        assert result["fragment_id"] == "frag_123"
        orchestrator.auto_classifier.classify_and_store.assert_called_once()
            
    def test_classify_compressed_memory_failure_retry(self, orchestrator, tmp_path):
        """测试分类失败并写入待处理"""
        # 构造足够长的脚本
        script = "User: Error test scenario. I want to test the retry mechanism when the API fails initially. This should be long enough."
        orchestrator.pending_path = str(tmp_path / "pending.json")
        
        # 第一次调用失败
        orchestrator.auto_classifier.classify_and_store.side_effect = Exception("API Error")
        
        result = orchestrator.classify_compressed_memory(script)
        
        assert result["success"] == 0
        assert result["failed"] == 1
        
        # 验证写入了 pending 文件
        import os
        assert os.path.exists(orchestrator.pending_path)
        
        # 第二次调用成功 (重试)
        orchestrator.auto_classifier.classify_and_store.side_effect = None
        orchestrator.auto_classifier.classify_and_store.return_value = "frag_retry_ok"
        
        orchestrator._retry_pending()
        
        # 验证 pending 文件被删除
        assert not os.path.exists(orchestrator.pending_path)
