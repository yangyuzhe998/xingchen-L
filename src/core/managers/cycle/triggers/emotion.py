from .base import BaseTrigger
from src.utils.logger import logger

class EmotionTrigger(BaseTrigger):
    """
    基于情绪波动的触发器
    监听 driver_response 中的 meta 信息
    """
    def check(self, event) -> bool:
        if event.type == "driver_response":
            meta = event.meta
            if meta and "user_emotion_detect" in meta:
                emotion = meta["user_emotion_detect"]
                # 负面情绪列表
                negative_emotions = ["angry", "sad", "fear"]
                
                if emotion in negative_emotions:
                    logger.info(f"[{self.name}] 检测到强烈负面情绪: {emotion}")
                    self._trigger(f"Negative Emotion Detected: {emotion}")
                    return True
        return False
