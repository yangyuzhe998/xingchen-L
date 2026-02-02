from .core.engine import PsycheEngine
from .services.mind_link import MindLink

# Singletons
psyche_engine = PsycheEngine()
mind_link = MindLink()

__all__ = ["PsycheEngine", "MindLink", "psyche_engine", "mind_link"]
