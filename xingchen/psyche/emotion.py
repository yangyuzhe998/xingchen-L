import yaml
import os
from typing import Dict, List
from xingchen.config.settings import settings

class EmotionDetector:
    """
    情绪检测器 (Emotion Detector)
    从文本中提取情感倾向，并根据规则返回情绪增量。
    """
    def __init__(self, rules_path: str = None):
        if rules_path is None:
            rules_path = os.path.join(settings.PROJECT_ROOT, "xingchen", "config", "emotion_rules.yaml")
        
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                self.rules = yaml.safe_load(f)
        except Exception:
            # 兜底默认规则
            self.rules = {
                "user_sentiment": {
                    "positive": ["谢谢", "好厉害", "太棒了"],
                    "negative": ["不对", "笨", "垃圾"],
                    "question_suffixes": ["?", "？", "呢", "吗"]
                },
                "emotion_deltas": {
                    "user_positive": {"achievement": 0.2, "anticipation": 0.1},
                    "user_negative": {"grievance": 0.3, "frustration": 0.1}
                }
            }
            
    def detect_user_sentiment(self, text: str) -> Dict[str, float]:
        """检测用户情感并返回情绪增量"""
        delta = {}
        text_lower = text.lower()
        
        sentiment_rules = self.rules.get("user_sentiment", {})
        deltas = self.rules.get("emotion_deltas", {})
        
        # 正向关键词
        if any(w in text_lower for w in sentiment_rules.get("positive", [])):
            pos_delta = deltas.get("user_positive", {})
            for emo, val in pos_delta.items():
                delta[emo] = delta.get(emo, 0) + val
                
        # 负向关键词
        if any(w in text_lower for w in sentiment_rules.get("negative", [])):
            neg_delta = deltas.get("user_negative", {})
            for emo, val in neg_delta.items():
                delta[emo] = delta.get(emo, 0) + val
                
        return delta

    def get_question_suffixes(self) -> List[str]:
        return self.rules.get("user_sentiment", {}).get("question_suffixes", ["?", "？", "呢", "吗"])

    def get_tool_deltas(self, success: bool) -> Dict[str, float]:
        deltas = self.rules.get("emotion_deltas", {})
        return deltas.get("tool_success" if success else "tool_failed", {})

    def get_value_conflict_deltas(self) -> Dict[str, float]:
        return self.rules.get("emotion_deltas", {}).get("value_conflict", {})
    
    def get_baseline_drift_mapping(self) -> Dict[str, Dict[str, float]]:
        return self.rules.get("baseline_drift_mapping", {})
