"""
测试自动分类器模块
"""
import pytest
from unittest.mock import Mock, patch
from xingchen.memory.services.auto_classifier import AutoClassifier


class TestAutoClassifier:
    """测试 AutoClassifier"""
    
    @pytest.fixture
    def mock_llm_response(self):
        """模拟 LLM 返回的分类结果"""
        # 模拟新的 LLMClient.chat 返回的对象，具有 content 属性
        mock_msg = Mock()
        mock_msg.content = '''```json
{
    "topic_name": "Python编程",
    "topic_description": "关于Python语言的学习和讨论",
    "is_new_topic": true,
    "task_name": "异步编程",
    "task_description": "async/await相关内容",
    "confidence": 0.9,
    "reason": "内容明确提到Python编程和异步编程"
}
```'''
        return mock_msg
    
    def test_classify_parses_response(self, mock_llm_response, tmp_path):
        """测试分类结果解析"""
        # 使用 patch 模拟 LLMClient
        with patch('xingchen.memory.services.auto_classifier.LLMClient') as MockLLM:
            mock_client = Mock()
            mock_client.chat.return_value = mock_llm_response
            MockLLM.return_value = mock_client
            
            # 使用 patch 模拟 topic_manager
            with patch('xingchen.memory.services.auto_classifier.topic_manager') as mock_tm:
                mock_tm.get_stats.return_value = {"topics": 0}
                mock_tm.create_topic.return_value = "topic_test123"
                mock_tm.create_task.return_value = "task_test456"
                mock_tm.search_topics.return_value = []
                
                # 创建实例并手动注入 mock
                classifier = AutoClassifier()
                classifier.llm = mock_client
                classifier.topic_manager = mock_tm
                
                result = classifier.classify("测试内容")
                
                assert result["topic_name"] == "Python编程"
                assert result["confidence"] == 0.9
                assert result["is_new"] == True
    
    def test_default_result_on_failure(self):
        """测试分类失败时返回默认结果"""
        with patch('xingchen.memory.services.auto_classifier.LLMClient') as MockLLM:
            mock_client = Mock()
            mock_client.chat.return_value = None  # 模拟失败
            MockLLM.return_value = mock_client
            
            with patch('xingchen.memory.services.auto_classifier.topic_manager') as mock_tm:
                mock_tm.get_stats.return_value = {"topics": 0}
                
                classifier = AutoClassifier()
                classifier.llm = mock_client
                classifier.topic_manager = mock_tm
                
                result = classifier.classify("测试内容")
                
                assert result["topic_name"] == "未分类"
                assert result["confidence"] == 0.0
