import os
from dotenv import load_dotenv
from openai import OpenAI
import sys

# 立即加载环境变量
load_dotenv(override=True)

class LLMClient:
    def __init__(self, provider="default"):
        self.provider = provider
        self.api_key = None
        self.base_url = None
        self.model = None
        self._configure()
        
        if not self.api_key:
            print(f"警告: 未找到提供商 {provider} 的 API Key")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def _configure(self):
        if self.provider == "deepseek":
            self.api_key = os.getenv("DEEPSEEK_API_KEY")
            self.base_url = os.getenv("DEEPSEEK_BASE_URL")
            self.model = "deepseek-chat"
        elif self.provider == "zhipu":
            self.api_key = os.getenv("ZHIPU_API_KEY")
            self.base_url = os.getenv("ZHIPU_BASE_URL")
            self.model = "glm-4" # 智谱默认模型
        elif self.provider == "qwen":
            self.api_key = os.getenv("QWEN_API_KEY")
            self.base_url = os.getenv("QWEN_BASE_URL")
            self.model = "qwen-turbo" # 通义千问默认模型
        else:
            # 默认为 OPENAI_* 变量（已配置为 DeepSeek）
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = os.getenv("OPENAI_BASE_URL")
            self.model = os.getenv("LLM_MODEL", "deepseek-chat")

    def chat(self, messages, temperature=0.7):
        """
        发送消息给 LLM 并获取回复。
        """
        try:
            print(f"[{self.provider}] 正在发送请求给 {self.model}...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM 错误: {e}")
            return f"错误: {str(e)}"

# 默认提供商的单例实例
default_client = LLMClient()
