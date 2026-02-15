
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from src.config.settings.settings import settings

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        # 如果日志目录不存在，则创建
        if not os.path.exists(settings.LOG_DIR):
            os.makedirs(settings.LOG_DIR)

        # 创建日志记录器
        self.logger = logging.getLogger("XingChen-V")
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        self.logger.propagate = False # 防止如果附加到 root logger 时重复记录

        # 检查 handlers 是否已存在，避免重复添加
        if not self.logger.handlers:
            # 日志格式
            formatter = logging.Formatter(
                '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # 文件处理器 (轮转日志: 最大10MB, 保留5个备份)
            file_handler = RotatingFileHandler(
                settings.LOG_FILE,
                maxBytes=10*1024*1024,
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

            # 控制台处理器 (在 Windows 上强制使用 UTF-8 输出以避免乱码)
            import io
            # 重新包装 sys.stdout 以支持 UTF-8
            # if sys.platform == 'win32':
            #     try:
            #         sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            #         sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            #     except (AttributeError, io.UnsupportedOperation):
            #         pass # 某些环境可能不支持重包装

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

            # 添加处理器
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def get_logger(self):
        return self.logger

# 全局访问器
logger = Logger().get_logger()
