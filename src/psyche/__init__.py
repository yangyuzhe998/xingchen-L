from typing import Optional

from .core.engine import PsycheEngine
from .services.mind_link import MindLink


_psyche_engine_instance: Optional[PsycheEngine] = None
_mind_link_instance: Optional[MindLink] = None


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


class _PsycheEngineProxy(PsycheEngine):
    """延迟初始化代理类（继承以通过 isinstance 检查）。"""

    def __init__(self):
        # 覆盖父类 __init__，防止 import 时触发文件读写与目录创建
        pass

    def __getattribute__(self, name):
        if name in ("__class__", "__instancecheck__", "__subclasscheck__"):
            return super().__getattribute__(name)
        return getattr(get_psyche_engine(), name)


class _MindLinkProxy(MindLink):
    """延迟初始化代理类（继承以通过 isinstance 检查）。"""

    def __init__(self):
        # 覆盖父类 __init__，防止 import 时触发文件读写与目录创建
        pass

    def __getattribute__(self, name):
        if name in ("__class__", "__instancecheck__", "__subclasscheck__"):
            return super().__getattribute__(name)
        return getattr(get_mind_link(), name)


# 全局代理（保持原 import 使用方式不变）
psyche_engine = _PsycheEngineProxy()
mind_link = _MindLinkProxy()

__all__ = [
    "PsycheEngine",
    "MindLink",
    "get_psyche_engine",
    "get_mind_link",
    "psyche_engine",
    "mind_link",
]
