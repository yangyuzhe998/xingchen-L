from ....config.prompts.prompts import (
    NAVIGATOR_SYSTEM_PROMPT, 
    SYSTEM_ARCHITECTURE_CONTEXT
)
from ....psyche import psyche_engine
from datetime import datetime

class ContextManager:
    """
    上下文管家 (ContextManager)
    职责：准备静态和动态上下文
    """
    def __init__(self, memory):
        self.memory = memory

    def build_static_context(self):
        """
        构建静态上下文 (Static Context)
        """
        # 使用配置中定义的中文架构描述
        project_context = SYSTEM_ARCHITECTURE_CONTEXT
        # 使用 safe_format 或简单的 replace 以避免 Key Error (因为 JSON 格式包含花括号)
        static_prompt = NAVIGATOR_SYSTEM_PROMPT.replace("{project_context}", project_context)
        return static_prompt

    def prepare_compression_context(self, events):
        """准备记忆压缩的动态上下文"""
        # 构建事件上下文
        script = ""
        for e in events:
            # 处理 Payload: 可能是对象也可能是字典
            payload = e.payload
            if hasattr(payload, 'model_dump'):
                payload_dict = payload.model_dump()
            elif hasattr(payload, 'dict'):
                payload_dict = payload.dict()
            else:
                payload_dict = payload if isinstance(payload, dict) else {}

            content = payload_dict.get('content', '')
            script += f"[{e.type}]: {content}\n"

        # [时间感知注入]
        now = datetime.now()
        # [Fix] 正确访问 Memory Service 中的 last_diary_time
        last_time = self.memory.service.last_diary_time if hasattr(self.memory.service, 'last_diary_time') else now
        time_delta = now - last_time
        seconds_passed = int(time_delta.total_seconds())
        
        # 将秒数转换为易读格式
        if seconds_passed < 60:
            time_str = f"{seconds_passed}秒"
        elif seconds_passed < 3600:
            time_str = f"{seconds_passed // 60}分钟"
        else:
            time_str = f"{seconds_passed // 3600}小时"

        time_context = (
            f"\n[时间感知]\n"
            f"- 当前时刻: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- 上次记录: {last_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- 逝去时间: {time_str}\n"
        )

        # 读取当前心智状态
        current_psyche = psyche_engine.get_state_summary()
        
        return script, time_context, current_psyche
