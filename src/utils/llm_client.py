import os
import time
from dotenv import load_dotenv
from openai import OpenAI
import uuid
from src.config.settings import settings
from src.utils.logger import logger

# 立即加载环境变量
load_dotenv(override=True)


class LLMClient:
    def __init__(self, provider=None):
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER
        self.api_key = None
        self.base_url = None
        self.model = None
        self._configure()

        if not self.api_key:
            logger.warning(f"警告: 未找到提供商 {self.provider} 的 API Key")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def _configure(self):
        if self.provider == "deepseek":
            self.api_key = os.getenv("DEEPSEEK_API_KEY")
            self.base_url = os.getenv("DEEPSEEK_BASE_URL")
            # 切换为 deepseek-reasoner (R1) 或 deepseek-chat (V3)
            self.model = settings.DEFAULT_LLM_MODEL
        elif self.provider == "zhipu":
            self.api_key = os.getenv("ZHIPU_API_KEY")
            self.base_url = os.getenv("ZHIPU_BASE_URL")
            self.model = "glm-4"  # 智谱默认模型
        elif self.provider == "qwen":
            self.api_key = os.getenv("QWEN_API_KEY")
            self.base_url = os.getenv("QWEN_BASE_URL")
            self.model = "qwen-turbo"  # 通义千问默认模型
        else:
            # 默认为 OPENAI_* 变量（已配置为 DeepSeek）
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = os.getenv("OPENAI_BASE_URL")
            self.model = os.getenv("LLM_MODEL", settings.DEFAULT_LLM_MODEL)

    def complete(self, prompt: str, **kwargs):
        """
        简单的文本补全 (Compatibility wrapper)
        """
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def chat(
        self,
        messages,
        temperature=0.7,
        trace_id=None,
        tools=None,
        tool_choice=None,
        max_retries: int = 2,
        retry_backoff_base: float = 1.0,
    ):
        """
        发送消息给 LLM 并获取回复。
        支持 trace_id 追踪。
        支持 Function Calling (Tools)。
        支持失败重试（指数退避）。

        :param max_retries: 最大重试次数（不含首次尝试）。例如 2 表示最多 1+2=3 次请求。
        :param retry_backoff_base: 指数退避基数秒数，例如 1.0 -> 1s, 2s, 4s...
        """
        if not trace_id:
            trace_id = str(uuid.uuid4())[:8]

        msg_len = sum(len(m.get("content", "") or "") for m in messages)
        tool_info = f", Tools: {len(tools)}" if tools else ""

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "timeout": settings.DEFAULT_LLM_TIMEOUT,
        }

        if tools:
            kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                if attempt == 0:
                    logger.info(
                        f"[{self.provider}] [TraceID: {trace_id}] Sending to {self.model}... (Msg: {len(messages)}, Chars: {msg_len}{tool_info})"
                    )
                else:
                    logger.warning(
                        f"[{self.provider}] [TraceID: {trace_id}] Retry {attempt}/{max_retries} sending to {self.model}... (Msg: {len(messages)}, Chars: {msg_len}{tool_info})"
                    )

                response = self.client.chat.completions.create(**kwargs)
                message = response.choices[0].message

                # 如果使用了 Tools，返回完整的 message 对象以便处理 tool_calls
                if tools:
                    logger.info(
                        f"[{self.provider}] [TraceID: {trace_id}] Received response (Tool Calls: {len(message.tool_calls) if message.tool_calls else 0})."
                    )
                    return message

                content = message.content
                logger.info(
                    f"[{self.provider}] [TraceID: {trace_id}] Received response ({len(content) if content else 0} chars)."
                )
                return content
            except Exception as e:
                last_error = e

                if attempt < max_retries:
                    wait_time = retry_backoff_base * (2**attempt)
                    logger.warning(
                        f"[{self.provider}] [TraceID: {trace_id}] Error on attempt {attempt + 1}/{max_retries + 1}, retrying in {wait_time:.1f}s: {e}"
                    )
                    time.sleep(wait_time)
                    continue

                logger.error(
                    f"[{self.provider}] [TraceID: {trace_id}] Error (max retries reached): {e}",
                    exc_info=True,
                )
                return None

        # 理论上不会到这里
        logger.error(
            f"[{self.provider}] [TraceID: {trace_id}] Error (unexpected retry loop exit): {last_error}",
            exc_info=True,
        )
        return None


# 默认提供商的单例实例
default_client = LLMClient()
