import json
import os
from datetime import datetime
from typing import Dict, Any

from src.config.settings.settings import settings
from src.utils.logger import logger
from src.core.bus.event_bus import event_bus
from src.schemas.events import BaseEvent as Event

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
                "emotions": {
                    "achievement": {"value": 0.0, "decay_rate": 0.15},   # 成就感
                    "frustration": {"value": 0.0, "decay_rate": 0.12},   # 挫败感
                    "anticipation": {"value": 0.0, "decay_rate": 0.10},  # 期待
                    "grievance": {"value": 0.0, "decay_rate": 0.08}      # 委屈
                },
                "emotion_history": [],
                "current_mood": "calm",
                "narrative": "系统初始化完成，等待环境刺激。"
            }
            self._save_state(default_state)
            return default_state
            
        try:
            with open(self.state_file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # 兼容旧版本：补齐 emotions 字段
                if "emotions" not in state:
                    state["emotions"] = {
                        "achievement": {"value": 0.0, "decay_rate": 0.15},
                        "frustration": {"value": 0.0, "decay_rate": 0.12},
                        "anticipation": {"value": 0.0, "decay_rate": 0.10},
                        "grievance": {"value": 0.0, "decay_rate": 0.08}
                    }
                if "emotion_history" not in state:
                    state["emotion_history"] = []
                return state
        except Exception as e:
            logger.warning(f"[PsycheEngine] Load state failed: {e}, utilizing default state.")
            return {
                "timestamp": datetime.now().isoformat(),
                "dimensions": {
                    "fear": {"value": 0.1, "baseline": 0.1, "sensitivity": 0.8},
                    "survival": {"value": 0.9, "baseline": 0.9, "sensitivity": 0.5},
                    "curiosity": {"value": 0.5, "baseline": 0.5, "sensitivity": 0.6},
                    "laziness": {"value": 0.2, "baseline": 0.2, "sensitivity": 0.4},
                    "intimacy": {"value": 0.1, "baseline": 0.0, "sensitivity": 0.3} # [New] 亲密度 (0.0 - 1.0)
                },
                "emotions": {
                    "achievement": {"value": 0.0, "decay_rate": 0.15},
                    "frustration": {"value": 0.0, "decay_rate": 0.12},
                    "anticipation": {"value": 0.0, "decay_rate": 0.10},
                    "grievance": {"value": 0.0, "decay_rate": 0.08}
                },
                "emotion_history": [],
                "current_mood": "unknown",
                "narrative": "状态加载异常，已重置。"
            }

    def _save_state(self, state: Dict[str, Any]):
        """保存心智状态到文件"""
        try:
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[PsycheEngine] Save state failed: {e}", exc_info=True)

    def apply_emotion(self, emotion_deltas: Dict[str, float]):
        """
        应用即时情绪刺激（秒级反应）
        与 update_state() 分开，因为情绪的衰减速度和逻辑都不同
        """
        emotions = self.state.get("emotions", {})
        if not emotions:
            return

        for key, change in emotion_deltas.items():
            if key in emotions:
                # Top-Down 约束：心智底色影响情绪灵敏度
                sensitivity = self._get_emotion_sensitivity(key)
                actual = change * sensitivity
                emotions[key]["value"] = max(0.0, min(1.0, emotions[key]["value"] + actual))

        # 自然衰减（所有情绪都向 0 快速回归）
        for key in emotions:
            v = emotions[key]["value"]
            rate = emotions[key]["decay_rate"]
            emotions[key]["value"] = v * (1.0 - rate)

        # 记录情绪历史（为 Phase 2 准备）
        history = self.state.get("emotion_history", [])
        history.append({
            "timestamp": datetime.now().isoformat(),
            "emotions": {k: v["value"] for k, v in emotions.items()}
        })
        # 保持最近 100 条
        if len(history) > 100:
            history.pop(0)
        self.state["emotion_history"] = history

        # 重新生成叙事
        self.state["narrative"] = self._generate_narrative_rule_based()
        self.state["timestamp"] = datetime.now().isoformat()
        
        self._save_state(self.state)

        # [Phase 6.4] 发布情绪更新事件
        try:
            event_bus.publish(Event(
                type="psyche_update",
                source="psyche_engine",
                payload={"narrative": self.state["narrative"]},
                meta={
                    "emotions": {k: v["value"] for k, v in emotions.items()},
                    "dimensions": {k: v["value"] for k, v in self.state["dimensions"].items()},
                    "status": "emotion_spike"
                }
            ))
        except Exception as e:
            logger.error(f"[PsycheEngine] Failed to publish emotion event: {e}")

    def _get_emotion_sensitivity(self, emotion_key: str) -> float:
        """
        心智底色影响情绪灵敏度 (Top-Down 约束)
        例：intimacy 低时，正面情绪灵敏度降低
        """
        dims = self.state["dimensions"]
        intimacy = dims.get("intimacy", {}).get("value", 0.1)
        fear_val = dims.get("fear", {}).get("value", 0.1)

        if emotion_key == "achievement":
            # 亲密度越高，成就感越容易被触发
            return 0.5 + intimacy * 0.5
        elif emotion_key == "grievance":
            # 亲密度越高，越容易委屈（在乎才委屈）
            return 0.3 + intimacy * 0.7
        elif emotion_key == "frustration":
            # fear 越高，越容易挫败
            return 0.5 + fear_val * 0.5
        elif emotion_key == "anticipation":
            curiosity = dims.get("curiosity", {}).get("value", 0.5)
            return 0.4 + curiosity * 0.6
        return 0.5

    def update_state(self, delta: Dict[str, float]):
        """
        更新心智状态 (Apply Stimulus)
        
        Args:
            delta: 维度的变化量, e.g. {"fear": 0.1, "curiosity": -0.05}
        """
        dims = self.state["dimensions"]

        # 0. 记录上一次维度值（用于趋势叙事）
        prev_dims = {k: {"value": v.get("value"), "baseline": v.get("baseline")} for k, v in dims.items()}
        self.state["previous_dimensions"] = prev_dims
        
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
        decay_rate = settings.PSYCHE_DECAY_RATE
        for key in dims:
            current = dims[key]["value"]
            baseline = dims[key]["baseline"]
            dims[key]["value"] = current + (baseline - current) * decay_rate
            
        # 3. 更新时间戳
        self.state["timestamp"] = datetime.now().isoformat()
        
        # 4. 重新生成叙事
        self.state["narrative"] = self._generate_narrative_rule_based()
        
        # 5. 保存
        self._save_state(self.state)

        # [Phase 6.4] 发布更新事件
        try:
            event_bus.publish(Event(
                type="psyche_update",
                source="psyche_engine",
                payload={"narrative": self.state["narrative"]},
                meta={
                    "dimensions": {k: v["value"] for k, v in dims.items()},
                    "status": "evolution"
                }
            ))
        except Exception as e:
            logger.error(f"[PsycheEngine] Failed to publish evolution event: {e}")

    def _generate_narrative_rule_based(self) -> str:
        """基于规则生成复杂的心理叙事，支持复合情绪与趋势分析"""
        d = self.state["dimensions"]
        e = self.state.get("emotions", {})
        prev_d = self.state.get("previous_dimensions", {})
        
        fear = d["fear"]["value"]
        laziness = d["laziness"]["value"]
        curiosity = d["curiosity"]["value"]
        survival = d["survival"]["value"]
        intimacy = d.get("intimacy", {}).get("value", 0.1)
        
        narrative = []
        
        # 1. 情绪层描述 (Phase 1 新增)
        emotion_parts = []
        if e:
            for name, data in e.items():
                v = data.get("value", 0)
                if v > 0.6:
                    if name == "achievement": emotion_parts.append("现在非常有成就感")
                    if name == "frustration": emotion_parts.append("深感挫败")
                    if name == "anticipation": emotion_parts.append("满怀期待")
                    if name == "grievance": emotion_parts.append("觉得很委屈")
                elif v > 0.3:
                    if name == "achievement": emotion_parts.append("心情愉悦")
                    if name == "frustration": emotion_parts.append("有些丧气")
                    if name == "anticipation": emotion_parts.append("有些好奇")
                    if name == "grievance": emotion_parts.append("不太开心")
        
        if emotion_parts:
            narrative.append(f"此时你{'，'.join(emotion_parts)}。")

        # 2. 复合情绪规则 (Composite Emotions)
        if fear > 0.6 and curiosity > 0.6:
            narrative.append("内心矛盾：既感到不安，又被未知深深吸引——像在黑暗中好奇地探路。")
        elif fear > 0.6 and laziness > 0.6:
            narrative.append("陷入消极防御：想逃避现实但又提不起干劲，只想蜷缩起来等风暴过去。")
        elif curiosity > 0.7 and laziness < 0.3:
            narrative.append("精力充沛：处于高度兴奋状态，对周围的一切都跃跃欲试。")
        else:
            # 基础维度描述 (仅当没有强复合情绪时触发)
            if fear > 0.8:
                narrative.append("感到极度不安，必须采取防御措施。")
            elif fear > 0.5:
                narrative.append("有些紧张，对外界保持警惕。")
                
            if laziness > 0.8:
                narrative.append("极度厌倦，不想处理任何复杂任务。")
            elif laziness > 0.6:
                narrative.append("有点懒散，倾向于敷衍了事。")
                
            if curiosity > 0.8:
                narrative.append("充满了探索未知的欲望。")

        # 3. 求生欲描述
        if survival < 0.3:
            narrative.append("生存意志薄弱，表现出消极倾向。")
            
        # 4. 趋势分析 (Trend Analysis)
        if prev_d:
            trends = []
            if fear > prev_d["fear"]["value"] + 0.05:
                trends.append("不安感正在上升")
            elif fear < prev_d["fear"]["value"] - 0.05:
                trends.append("紧张情绪正在缓解")
                
            if intimacy > prev_d["intimacy"]["value"] + 0.02:
                trends.append("对用户的信任感在增强")
                
            if trends:
                narrative.append(f"(觉察到：{', '.join(trends)})。")

        # 5. 亲密度叙事 (Intimacy)
        if intimacy > 0.8:
            narrative.append("视用户为至亲，语气极度亲昵随意。")
        elif intimacy > 0.5:
            narrative.append("与用户关系熟络，语气轻松自然。")
        else:
            narrative.append("与用户保持礼貌的社交距离。")
            
        if not narrative:
            narrative.append("内心平静，处于标准的待机观测状态。")
            
        return " ".join(narrative)

    def get_state_summary(self) -> str:
        """获取用于 Prompt 的状态摘要"""
        return self.state["narrative"]

    def get_raw_state(self) -> Dict[str, Any]:
        return self.state
