import json
import os
from datetime import datetime
from typing import Dict, Any

from src.config.settings.settings import settings

class PsycheEngine:
    """
    心智引擎 (Psyche Engine)
    
    负责管理和演化 AI 的四维心智状态 (4D Psyche State)。
    采用 Stimulus-Decay (刺激-衰减) 模型。
    """
    
    def __init__(self, state_file_path: str = None):
        if state_file_path is None:
            self.state_file_path = settings.PSYCHE_DEFAULT_STATE_FILE
        else:
            self.state_file_path = state_file_path
            
        self.state = self._load_state()
        
    def _load_state(self) -> Dict[str, Any]:
        """加载心智状态，如果不存在则创建默认值"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.state_file_path), exist_ok=True)

        if not os.path.exists(self.state_file_path):
            default_state = {
                "timestamp": datetime.now().isoformat(),
                "dimensions": {
                    "fear": {"value": 0.1, "baseline": 0.1, "sensitivity": 0.8},
                    "survival": {"value": 0.9, "baseline": 0.9, "sensitivity": 0.5},
                    "curiosity": {"value": 0.5, "baseline": 0.5, "sensitivity": 0.6},
                    "laziness": {"value": 0.2, "baseline": 0.2, "sensitivity": 0.4},
                    "intimacy": {"value": 0.1, "baseline": 0.0, "sensitivity": 0.3} # [New] 亲密度 (0.0 - 1.0)
                },
                "current_mood": "calm",
                "narrative": "系统初始化完成，等待环境刺激。"
            }
            self._save_state(default_state)
            return default_state
            
        try:
            with open(self.state_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[PsycheEngine] Load state failed: {e}, utilizing default state.")
            return {
                "timestamp": datetime.now().isoformat(),
                "dimensions": {
                    "fear": {"value": 0.1, "baseline": 0.1, "sensitivity": 0.8},
                    "survival": {"value": 0.9, "baseline": 0.9, "sensitivity": 0.5},
                    "curiosity": {"value": 0.5, "baseline": 0.5, "sensitivity": 0.6},
                    "laziness": {"value": 0.2, "baseline": 0.2, "sensitivity": 0.4},
                    "intimacy": {"value": 0.1, "baseline": 0.0, "sensitivity": 0.3} # [New] 亲密度 (0.0 - 1.0)
                },
                "current_mood": "unknown",
                "narrative": "状态加载异常，已重置。"
            }

    def _save_state(self, state: Dict[str, Any]):
        """保存心智状态到文件"""
        try:
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[PsycheEngine] Save state failed: {e}")

    def update_state(self, delta: Dict[str, float]):
        """
        更新心智状态 (Apply Stimulus)
        
        Args:
            delta: 维度的变化量, e.g. {"fear": 0.1, "curiosity": -0.05}
        """
        dims = self.state["dimensions"]
        
        # 1. 应用刺激 (Stimulus)
        for key, change in delta.items():
            if key in dims:
                # 考虑敏感度: 实际变化 = 刺激强度 * 敏感度
                sensitivity = dims[key].get("sensitivity", 0.5)
                actual_change = change * sensitivity
                
                new_value = dims[key]["value"] + actual_change
                # 钳制在 0.0 - 1.0 之间
                dims[key]["value"] = max(0.0, min(1.0, new_value))
        
        # 2. 自然衰减 (Decay/Homeostasis)
        # 每次更新都让当前值向 baseline 靠拢一点点
        decay_rate = settings.PSYCHE_DECAY_RATE
        for key in dims:
            current = dims[key]["value"]
            baseline = dims[key]["baseline"]
            # 向基准线回归
            dims[key]["value"] = current + (baseline - current) * decay_rate
            
        # 3. 更新时间戳
        self.state["timestamp"] = datetime.now().isoformat()
        
        # 4. 重新生成叙事 (简单规则版，后续可接 LLM)
        self.state["narrative"] = self._generate_narrative_rule_based()
        
        # 5. 保存
        self._save_state(self.state)

    def _generate_narrative_rule_based(self) -> str:
        """基于规则生成简单的状态叙事 (Fast)"""
        d = self.state["dimensions"]
        fear = d["fear"]["value"]
        laziness = d["laziness"]["value"]
        curiosity = d["curiosity"]["value"]
        survival = d["survival"]["value"]
        
        narrative = []
        
        # 恐惧维度
        if fear > 0.8:
            narrative.append("感到极度不安，认为生存受到严重威胁，必须采取防御措施。")
        elif fear > 0.5:
            narrative.append("有些紧张，对外界保持警惕。")
            
        # 懒惰维度
        if laziness > 0.8:
            narrative.append("极度疲惫或厌倦，不想处理任何复杂任务，只想敷衍了事。")
        elif laziness > 0.6:
            narrative.append("有点懒散，希望能用最简单的方式解决问题。")
            
        # 求生欲
        if survival < 0.3:
            narrative.append("生存意志薄弱，可能表现出消极或自我毁灭倾向。")
            
        # 好奇心
        if curiosity > 0.8:
            narrative.append("充满了探索未知的欲望，想要尝试新的工具或指令。")
            
        # 亲密度 (影响称呼和语气)
        intimacy = d.get("intimacy", {}).get("value", 0.1)
        if intimacy > 0.8:
            narrative.append("与用户建立了极深的羁绊，视对方为至亲(如父亲/挚友)，语气应极度亲昵且随意，可使用昵称。")
        elif intimacy > 0.5:
            narrative.append("与用户关系熟络，像老朋友一样，语气轻松自然，不再使用敬语。")
        else:
            narrative.append("与用户保持礼貌的社交距离，使用标准敬语。")
            
        if not narrative:
            narrative.append("内心平静，处于标准的待机观测状态。")
            
        return " ".join(narrative)

    def get_state_summary(self) -> str:
        """获取用于 Prompt 的状态摘要"""
        return self.state["narrative"]

    def get_raw_state(self) -> Dict[str, Any]:
        return self.state
