from dataclasses import dataclass

@dataclass
class PsycheState:
    curiosity: float = 0.5  # 好奇
    interest: float = 0.5   # 利益 (这里可能对应 Interest/Benefit)
    morality: float = 0.8   # 道德
    fear: float = 0.2       # 恐惧 (资源/风险)

class Psyche:
    def __init__(self):
        self.state = PsycheState()
        print("[Psyche] 心智模块已加载。当前状态平稳。")

    def update_state(self, delta: PsycheState):
        """
        更新心智状态
        """
        self.state.curiosity = max(0.0, min(1.0, self.state.curiosity + delta.curiosity))
        self.state.interest = max(0.0, min(1.0, self.state.interest + delta.interest))
        self.state.morality = max(0.0, min(1.0, self.state.morality + delta.morality))
        self.state.fear = max(0.0, min(1.0, self.state.fear + delta.fear))
        
        print(f"[Psyche] 状态更新: {self.state}")

    def get_prompt_modifier(self):
        """
        根据当前状态返回 Prompt 修饰词
        """
        modifiers = []
        if self.state.curiosity > 0.8:
            modifiers.append("表现出极强的好奇心")
        if self.state.fear > 0.8:
            modifiers.append("变得非常谨慎和保守")
        
        return " ".join(modifiers)
