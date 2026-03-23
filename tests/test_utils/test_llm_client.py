"""
测试 xingchen/utils/llm_client.py
验证 LLMClient 功能：配置、提供商、API 调用（Mock）

注意：真实 API 调用需要有效的 API Key，这里主要测试配置和结构
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from xingchen.utils.llm_client import LLMClient


class TestLLMClientConfiguration:
    """测试 LLMClient 配置"""
    
    def test_llm_client_init_default(self):
        """测试默认初始化"""
        client = LLMClient()
        
        assert client is not None
        assert client.provider is not None
        assert client.client is not None
        
        print(f"✅ LLMClient 默认初始化成功，提供商: {client.provider}")
    
    def test_llm_client_has_required_attributes(self):
        """测试必要属性存在"""
        client = LLMClient()
        
        assert hasattr(client, 'provider')
        assert hasattr(client, 'api_key')
        assert hasattr(client, 'base_url')
        assert hasattr(client, 'model')
        assert hasattr(client, 'client')
        
        print(f"✅ LLMClient 必要属性存在")
    
    def test_llm_client_deepseek_provider(self):
        """测试 DeepSeek 提供商配置"""
        client = LLMClient(provider="deepseek")
        
        assert client.provider == "deepseek"
        # model 应该从 settings 获取
        assert client.model is not None
        
        print(f"✅ DeepSeek 提供商配置成功，模型: {client.model}")
    
    def test_llm_client_zhipu_provider(self):
        """测试智谱提供商配置"""
        client = LLMClient(provider="zhipu")
        
        assert client.provider == "zhipu"
        # v3.0 默认模型已从 settings 获取
        assert client.model is not None
        
        print(f"✅ 智谱提供商配置成功")
    
    def test_llm_client_qwen_provider(self):
        """测试通义千问提供商配置"""
        client = LLMClient(provider="qwen")
        
        assert client.provider == "qwen"
        # v3.0 默认模型已从 settings 获取
        assert client.model is not None
        
        print(f"✅ 通义千问提供商配置成功")


class TestLLMClientMethods:
    """测试 LLMClient 方法"""
    
    def test_llm_client_has_chat_method(self):
        """测试 chat 方法存在"""
        client = LLMClient()
        
        assert hasattr(client, 'chat')
        assert callable(client.chat)
        
        print(f"✅ chat 方法存在")


class TestLLMClientMockCalls:
    """测试 LLMClient API 调用（Mock）"""
    
    @patch('xingchen.utils.llm_client.OpenAI')
    def test_llm_client_chat_mock(self, mock_openai):
        """测试 chat 方法（Mock）"""
        # 设置 mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "这是模拟的回复"
        mock_message.tool_calls = None
        
        # 模拟 OpenAI 的层级结构
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = LLMClient()
        # 强制替换内部 client 为 mock
        client.client = mock_client
        
        result = client.chat([{"role": "user", "content": "你好"}])
        
        assert result is not None
        assert result.content == "这是模拟的回复"
        assert mock_client.chat.completions.create.called
        
        print(f"✅ chat 方法 Mock 调用成功")
