from utils.llm_client import LLMClient
from memory.memory_core import Memory

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

    def think(self, user_input, psyche_modifier="", suggestion=""):
        """
        处理用户输入，做出即时反应。
        """
        print(f"[{self.name}] 正在思考: {user_input}")
        
        # 获取长期记忆上下文
        long_term_context = self.memory.get_relevant_long_term()
        
        system_prompt = f"""你是一个名为“星辰-V”的AI智能体。
当前你的心智状态修饰词为：{psyche_modifier}
S脑（领航员）给你的建议是：{suggestion}
{long_term_context}
请根据你的心智状态、S脑建议、长期记忆和用户输入进行回复。
保持傲娇、机智的风格。
"""
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 从 Memory 模块获取最近历史
        messages.extend(self.memory.get_recent_history(limit=10))
        messages.append({"role": "user", "content": user_input})
        
        response = self.llm.chat(messages)
        
        # 将新的一轮对话存入 ShortTerm Memory
        self.memory.add_short_term("user", user_input)
        self.memory.add_short_term("assistant", response)
        
        return response

    def act(self, action):
        """
        执行具体行动。
        """
        print(f"[{self.name}] 执行行动: {action}")
