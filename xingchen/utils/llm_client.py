import os
import time
from dotenv import load_dotenv
from openai import OpenAI
import uuid
from xingchen.config.settings import settings
from xingchen.utils.logger import logger

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
            self.model = settings.DEFAULT_LLM_MODEL
        elif self.provider == "zhipu":
            self.api_key = os.getenv("ZHIPU_API_KEY")
            self.base_url = os.getenv("ZHIPU_BASE_URL")
            self.model = settings.ZHIPU_DEFAULT_MODEL
        elif self.provider == "qwen":
            self.api_key = os.getenv("QWEN_API_KEY")
            self.base_url = os.getenv("QWEN_BASE_URL")
            self.model = settings.QWEN_DEFAULT_MODEL
        else:
            # 默认为 OPENAI_* 变量
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
                        f"[{self.provider}] [TraceID: {trace_id}] Retry attempt {attempt}/{max_retries}..."
                    )

                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message

            except Exception as e:
                last_error = e
                logger.error(f"[{self.provider}] [TraceID: {trace_id}] Error: {e}")
                if attempt < max_retries:
                    sleep_time = retry_backoff_base * (2 ** attempt)
                    time.sleep(sleep_time)
                else:
                    break

        raise last_error
