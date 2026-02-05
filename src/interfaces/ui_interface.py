
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable

class UserInterface:
    """
    用户界面抽象基类 (Mixin)
    定义了前端必须实现的接口，以便与后端 (Driver/Navigator) 解耦。
    注意：不继承 ABC，避免与 Textual App (已有 metaclass) 冲突。
    """

    def display_message(self, role: str, content: str, meta: Dict[str, Any] = None):
        """
        显示一条消息
        :param role: "user" | "assistant" | "system"
        :param content: 消息内容
        :param meta: 元数据 (如情绪、内心独白)
        """
        raise NotImplementedError

    def set_input_handler(self, handler: Callable[[str], None]):
        """
        设置用户输入的处理函数
        :param handler: 当用户输入时调用的回调函数 func(input_text)
        """
        raise NotImplementedError

    def update_status(self, status: str, details: Dict[str, Any] = None):
        """
        更新系统状态显示
        :param status: 状态文本 (e.g. "Thinking...", "Idle")
        :param details: 详细信息 (e.g. {"cpu": "10%", "mood": "happy"})
        """
        raise NotImplementedError

    def run(self):
        """
        启动界面主循环 (Blocking)
        """
        raise NotImplementedError
