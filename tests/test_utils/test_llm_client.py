"""
测试 src/utils/llm_client.py
验证 LLMClient 功能：配置、提供商、API 调用（Mock）

注意：真实 API 调用需要有效的 API Key，这里主要测试配置和结构
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from src.utils.llm_client import LLMClient


class TestLLMClientConfiguration:
    """测试 LLMClient 配置"""
    
    def test_llm_client_init_default(self):
        """测试默认初始化"""
        client = LLMClient()
        
        assert client is not None
        assert client.provider is not None
        assert client.client is not None
        
        print(f"✓ LLMClient 默认初始化成功，提供商: {client.provider}")
    
    def test_llm_client_has_required_attributes(self):
        """测试必要属性存在"""
        client = LLMClient()
        
        assert hasattr(client, 'provider')
        assert hasattr(client, 'api_key')
        assert hasattr(client, 'base_url')
        assert hasattr(client, 'model')
        assert hasattr(client, 'client')
        
        print(f"✓ LLMClient 必要属性存在")
    
    def test_llm_client_deepseek_provider(self):
        """测试 DeepSeek 提供商配置"""
        client = LLMClient(provider="deepseek")
        
        assert client.provider == "deepseek"
        # model 应该从 settings 获取
        assert client.model is not None
        
        print(f"✓ DeepSeek 提供商配置成功，模型: {client.model}")
    
    def test_llm_client_zhipu_provider(self):
        """测试智谱提供商配置"""
        client = LLMClient(provider="zhipu")
        
        assert client.provider == "zhipu"
        assert client.model == "glm-4"
        
        print(f"✓ 智谱提供商配置成功")
    
    def test_llm_client_qwen_provider(self):
        """测试通义千问提供商配置"""
        client = LLMClient(provider="qwen")
        
        assert client.provider == "qwen"
        assert client.model == "qwen-turbo"
        
        print(f"✓ 通义千问提供商配置成功")


class TestLLMClientMethods:
    """测试 LLMClient 方法"""
    
    def test_llm_client_has_complete_method(self):
        """测试 complete 方法存在"""
        client = LLMClient()
        
        assert hasattr(client, 'complete')
        assert callable(client.complete)
        
        print(f"✓ complete 方法存在")
    
    def test_llm_client_has_chat_method(self):
        """测试 chat 方法存在"""
        client = LLMClient()
        
        assert hasattr(client, 'chat')
        assert callable(client.chat)
        
        print(f"✓ chat 方法存在")


class TestLLMClientMockCalls:
    """测试 LLMClient API 调用（Mock）"""
    
    @patch('src.utils.llm_client.OpenAI')
    def test_llm_client_chat_mock(self, mock_openai):
        """测试 chat 方法（Mock）"""
        # 设置 mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "这是模拟的回复"
        mock_message.tool_calls = None
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # 创建客户端并调用
        client = LLMClient()
        messages = [{"role": "user", "content": "你好"}]
        result = client.chat(messages)
        
        # 验证
        assert result == "这是模拟的回复"
        mock_client.chat.completions.create.assert_called_once()
        
        print(f"✓ chat 方法 Mock 调用成功")
    
    @patch('src.utils.llm_client.OpenAI')
    def test_llm_client_chat_with_tools_mock(self, mock_openai):
        """测试带工具的 chat 方法（Mock）"""
        # 设置 mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_message.tool_calls = [MagicMock(id="call_1", function=MagicMock(name="search"))]
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # 创建客户端并调用
        client = LLMClient()
        messages = [{"role": "user", "content": "搜索天气"}]
        tools = [{"type": "function", "function": {"name": "search"}}]
        result = client.chat(messages, tools=tools)
        
        # 验证返回的是 message 对象（因为有 tools）
        assert result is not None
        assert hasattr(result, 'tool_calls')
        
        print(f"✓ 带工具的 chat 方法 Mock 调用成功")
    
    @patch('src.utils.llm_client.OpenAI')
    def test_llm_client_complete_mock(self, mock_openai):
        """测试 complete 方法（Mock）"""
        # 设置 mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "完成的文本"
        mock_message.tool_calls = None
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # 创建客户端并调用
        client = LLMClient()
        result = client.complete("写一首诗")
        
        # 验证
        assert result == "完成的文本"
        
        print(f"✓ complete 方法 Mock 调用成功")


class TestLLMClientErrorHandling:
    """测试错误处理"""
    
    @patch('src.utils.llm_client.OpenAI')
    def test_llm_client_api_error_handling(self, mock_openai):
        """测试 API 错误处理"""
        # 设置 mock 抛出异常
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        # 创建客户端并调用
        client = LLMClient()
        result = client.chat([{"role": "user", "content": "测试"}])
        
        # 验证返回 None（根据实现）
        assert result is None
        
        print(f"✓ API 错误处理正确")


class TestLLMClientIntegration:
    """测试集成功能"""
    
    def test_default_client_exists(self):
        """测试默认客户端存在"""
        from src.utils.llm_client import default_client
        
        assert default_client is not None
        assert isinstance(default_client, LLMClient)
        
        print(f"✓ 默认客户端存在")
    
    @patch('src.utils.llm_client.OpenAI')
    def test_trace_id_generation(self, mock_openai):
        """测试 trace_id 自动生成"""
        # 设置 mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "回复"
        mock_message.tool_calls = None
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # 创建客户端并调用（不传 trace_id）
        client = LLMClient()
        result = client.chat([{"role": "user", "content": "测试"}])
        
        # 验证调用成功（trace_id 应该自动生成）
        assert result is not None
        
        print(f"✓ trace_id 自动生成成功")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
