import json
import os
import threading
from datetime import datetime
from typing import Dict, Any, Optional

from xingchen.config.settings import settings
from xingchen.utils.logger import logger
from xingchen.core.event_bus import event_bus
from xingchen.schemas.events import BaseEvent as Event


class PsycheEngine:
    """
    心智引擎 (Psyche Engine)
    
    负责管理和演化 AI 的四维心智状态 (4D Psyche State)。
    采用 Stimulus-Decay (刺激-衰减) 模型。
    """
    
    def __init__(self, state_file_path: str = None):
        self._lock = threading.Lock()
        if state_file_path is None:
            self.state_file_path = settings.PSYCHE_DEFAULT_STATE_FILE
        else:
            self.state_file_path = state_file_path
            
        self.state = self._load_state()
        
    def _load_state(self) -> Dict[str, Any]:
        """加载心智状态，如果不存在则创建默认值"""
        os.makedirs(os.path.dirname(self.state_file_path), exist_ok=True)

        if not os.path.exists(self.state_file_path):
            default_state = {
                "timestamp": datetime.now().isoformat(),
                "dimensions": {
                    "fear": {"value": 0.1, "baseline": 0.1, "sensitivity": 0.8},
                    "survival": {"value": 0.9, "baseline": 0.9, "sensitivity": 0.5},
                    "curiosity": {"value": 0.5, "baseline": 0.5, "sensitivity": 0.6},
                    "laziness": {"value": 0.2, "baseline": 0.2, "sensitivity": 0.4},
                    "intimacy": {"value": 0.1, "baseline": 0.0, "sensitivity": 0.3}
                },
                "emotions": {
                    "achievement": {"value": 0.0, "decay_rate": 0.15},
                    "frustration": {"value": 0.0, "decay_rate": 0.12},
                    "anticipation": {"value": 0.0, "decay_rate": 0.10},
                    "grievance": {"value": 0.0, "decay_rate": 0.08}
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
                    "intimacy": {"value": 0.1, "baseline": 0.0, "sensitivity": 0.3}
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
        """应用即时情绪刺激（秒级反应）"""
        with self._lock:
            emotions = self.state.get("emotions", {})
            if not emotions:
                return

            for key, change in emotion_deltas.items():
                if key in emotions:
                    sensitivity = self._get_emotion_sensitivity(key)
                    actual = change * sensitivity
                    emotions[key]["value"] = max(0.0, min(1.0, emotions[key]["value"] + actual))

            # 自然衰减
            for key in emotions:
                v = emotions[key]["value"]
                rate = emotions[key]["decay_rate"]
                emotions[key]["value"] = v * (1.0 - rate)

            history = self.state.get("emotion_history", [])
            history.append({
                "timestamp": datetime.now().isoformat(),
                "emotions": {k: v["value"] for k, v in emotions.items()}
            })
            if len(history) > 100:
                history.pop(0)
            self.state["emotion_history"] = history

            self.state["narrative"] = self._generate_narrative_rule_based()
            self.state["timestamp"] = datetime.now().isoformat()
            
            self._save_state(self.state)

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

    def update_state(self, delta: Dict[str, float]):
        """更新心智状态 (Apply Stimulus)"""
        with self._lock:
            dims = self.state["dimensions"]
            prev_dims = {k: {"value": v.get("value"), "baseline": v.get("baseline")} for k, v in dims.items()}
            self.state["previous_dimensions"] = prev_dims
            
            for key, change in delta.items():
                if key in dims:
                    sensitivity = dims[key].get("sensitivity", 0.5)
                    actual_change = change * sensitivity
                    dims[key]["value"] = max(0.0, min(1.0, dims[key]["value"] + actual_change))
            
            decay_rate = settings.PSYCHE_DECAY_RATE
            for key in dims:
                current = dims[key]["value"]
                baseline = dims[key]["baseline"]
                dims[key]["value"] = current + (baseline - current) * decay_rate
                
            self.state["timestamp"] = datetime.now().isoformat()
            self.state["narrative"] = self._generate_narrative_rule_based()
            self._save_state(self.state)

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

    def get_raw_state(self) -> Dict[str, Any]:
        """线程安全地获取状态副本"""
        with self._lock:
            return json.loads(json.dumps(self.state)) # 深度拷贝

    def get_state_summary(self) -> str:
        """获取心智状态的叙事性总结"""
        with self._lock:
            return self.state.get("narrative", "心境平和。")

    def _get_emotion_sensitivity(self, emotion_key: str) -> float:
        dims = self.state["dimensions"]
        intimacy = dims.get("intimacy", {}).get("value", 0.1)
        fear_val = dims.get("fear", {}).get("value", 0.1)

        if emotion_key == "achievement":
            return 0.5 + intimacy * 0.5
        elif emotion_key == "grievance":
            return 0.3 + intimacy * 0.7
        elif emotion_key == "frustration":
            return 0.5 + fear_val * 0.5
        elif emotion_key == "anticipation":
            curiosity = dims.get("curiosity", {}).get("value", 0.5)
            return 0.4 + curiosity * 0.6
        return 0.5

    def _generate_narrative_rule_based(self) -> str:
        d = self.state["dimensions"]
        e = self.state.get("emotions", {})
        
        fear = d["fear"]["value"]
        laziness = d["laziness"]["value"]
        curiosity = d["curiosity"]["value"]
        survival = d["survival"]["value"]
        intimacy = d.get("intimacy", {}).get("value", 0.1)
        
        narrative = []
        
        emotion_parts = []
        if e:
            for name, data in e.items():
                v = data.get("value", 0)
                if v > 0.6:
                    if name == "achievement": emotion_parts.append("现在非常有成就感")
                    elif name == "frustration": emotion_parts.append("感到很挫败")
                    elif name == "anticipation": emotion_parts.append("满怀期待")
                    elif name == "grievance": emotion_parts.append("心里觉得有些委屈")
        
        if emotion_parts:
            narrative.append("，".join(emotion_parts) + "。")
        
        if fear > 0.7: narrative.append("感到严重的不安和警惕。")
        elif fear < 0.2: narrative.append("处于非常放松的状态。")
        
        if curiosity > 0.8: narrative.append("对未知充满了探索的渴望。")
        if laziness > 0.8: narrative.append("此刻只想静静呆着，不想处理复杂的事情。")
        
        if intimacy > 0.8: narrative.append("对当前互动的亲密度感到非常舒适。")
        
        return "".join(narrative) if narrative else "心境平和，波澜不惊。"
