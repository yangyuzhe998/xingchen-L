
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
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
        self.logger.propagate = False 

        if not self.logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # [Production Hardening] 按天滚动日志，保留 30 天
            file_handler = TimedRotatingFileHandler(
                settings.LOG_FILE,
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def get_logger(self):
        return self.logger

# 全局访问器
logger = Logger().get_logger()
