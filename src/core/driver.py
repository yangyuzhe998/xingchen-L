from utils.llm_client import LLMClient
from memory.memory_core import Memory
from core.bus import event_bus, Event
from config.prompts import DRIVER_SYSTEM_PROMPT
import json

class Driver:
    """
    F脑 (Fast Brain) / 快脑
    负责：实时交互、短期决策、具体行动。
    特点：反应快，直接控制输出，受 Psyche (心智) 影响。
    模型：Qwen (通义千问)
    """
    def __init__(self, name="Driver", memory=None):
        self.name = name
        # F脑使用 Qwen
        self.llm = LLMClient(provider="qwen")
        self.memory = memory if memory else Memory()
        print(f"[{self.name}] 初始化完成。模型: Qwen。")

    def think(self, user_input, psyche_state=None, suggestion=""):
        """
        处理用户输入，做出即时反应。
        """
        print(f"[{self.name}] 正在思考: {user_input}")
        
        # 获取长期记忆上下文 (传入 user_input 以进行关键词检索)
        long_term_context = self.memory.get_relevant_long_term(query=user_input)
        
        # 构造 Psyche 描述
        psyche_desc = ""
        if psyche_state:
            psyche_desc = f"好奇:{psyche_state.curiosity:.2f}, 利益:{psyche_state.interest:.2f}, 道德:{psyche_state.morality:.2f}, 恐惧:{psyche_state.fear:.2f}"
            # 也可以保留之前的 prompt_modifier 逻辑，这里为了演示 Meta 数据，直接用数值

        system_prompt = DRIVER_SYSTEM_PROMPT.format(
            psyche_desc=psyche_desc,
            suggestion=suggestion,
            long_term_context=long_term_context
        )
        
        messages = [
            {"role": "system", "content": system_prompt, "response_format": {"type": "json_object"}} 
        ]
        
        # 从 Memory 模块获取最近历史
        messages.extend(self.memory.get_recent_history(limit=10))
        messages.append({"role": "user", "content": user_input})
        
        # 发布 UserInput 事件到总线
        event_bus.publish(Event(
            type="user_input",
            source="user",
            payload={"content": user_input},
            meta={}
        ))

        raw_response = self.llm.chat(messages)
        
        # 解析 JSON 输出
        try:
            # 尝试清理可能存在的 markdown 代码块标记
            clean_response = raw_response.replace("```json", "").replace("```", "").strip()
            parsed_response = json.loads(clean_response)
            reply = parsed_response.get("reply", raw_response)
            inner_voice = parsed_response.get("inner_voice", "")
            emotion = parsed_response.get("emotion", "neutral")
        except Exception as e:
            print(f"[{self.name}] JSON解析失败，回退到原始文本: {e}")
            reply = raw_response
            inner_voice = "解析错误"
            emotion = "unknown"

        # 将新的一轮对话存入 ShortTerm Memory
        self.memory.add_short_term("user", user_input)
        self.memory.add_short_term("assistant", reply)
        
        # 发布 DriverResponse 事件到总线 (包含 Meta 数据)
        event_bus.publish(Event(
            type="driver_response",
            source="driver",
            payload={"content": reply},
            meta={
                "inner_voice": inner_voice,
                "user_emotion_detect": emotion,
                "psyche_state": str(psyche_state) if psyche_state else "unknown",
                "suggestion_ref": suggestion
            }
        ))
        
        return reply

    def act(self, action):
        """
        执行具体行动。
        """
        print(f"[{self.name}] 执行行动: {action}")
