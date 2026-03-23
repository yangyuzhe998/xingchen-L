from typing import Optional
from .engine import PsycheEngine
from .values import ValueSystem
from .mind_link import MindLink
from .emotion import EmotionDetector
from xingchen.utils.proxy import lazy_proxy

_psyche_engine_instance: Optional[PsycheEngine] = None
_mind_link_instance: Optional[MindLink] = None
_value_system_instance: Optional[ValueSystem] = None
_emotion_detector_instance: Optional[EmotionDetector] = None

def get_psyche_engine() -> PsycheEngine:
    """获取全局 PsycheEngine 实例（延迟初始化）。"""
    global _psyche_engine_instance
    if _psyche_engine_instance is None:
        _psyche_engine_instance = PsycheEngine()
    return _psyche_engine_instance

def get_mind_link() -> MindLink:
    """获取全局 MindLink 实例（延迟初始化）。"""
    global _mind_link_instance
    if _mind_link_instance is None:
        _mind_link_instance = MindLink()
    return _mind_link_instance

def get_value_system() -> ValueSystem:
    """获取全局 ValueSystem 实例（延迟初始化）。"""
    global _value_system_instance
    if _value_system_instance is None:
        _value_system_instance = ValueSystem()
    return _value_system_instance

def get_emotion_detector() -> EmotionDetector:
    """获取全局 EmotionDetector 实例（延迟初始化）。"""
    global _emotion_detector_instance
    if _emotion_detector_instance is None:
        _emotion_detector_instance = EmotionDetector()
    return _emotion_detector_instance

# 全局代理
psyche_engine = lazy_proxy(get_psyche_engine, PsycheEngine)
mind_link = lazy_proxy(get_mind_link, MindLink)
value_system = lazy_proxy(get_value_system, ValueSystem)
emotion_detector = lazy_proxy(get_emotion_detector, EmotionDetector)

__all__ = [
    "PsycheEngine",
    "MindLink",
    "ValueSystem",
    "EmotionDetector",
    "psyche_engine",
    "mind_link",
    "value_system",
    "emotion_detector",
    "get_psyche_engine",
    "get_mind_link",
    "get_value_system",
    "get_emotion_detector"
]
