"""
测试 xingchen/utils/logger.py
验证 Logger 功能：单例模式、文件处理、日志级别
"""

import pytest
import os
import logging
from pathlib import Path
from xingchen.utils.logger import Logger, logger


class TestLoggerSingleton:
    """测试单例模式"""
    
    def test_logger_is_singleton(self):
        """测试 Logger 是单例"""
        logger1 = Logger()
        logger2 = Logger()
        
        assert logger1 is logger2
        assert id(logger1) == id(logger2)
        
        print(f"✅ Logger 单例模式正常")
    
    def test_logger_instance_has_logger_attribute(self):
        """测试 Logger 实例含 logger 属性"""
        log_instance = Logger()
        
        assert hasattr(log_instance, 'logger')
        assert isinstance(log_instance.logger, logging.Logger)
        
        print(f"✅ Logger 实例属性正常")


class TestLoggerInitialization:
    """测试初始化"""
    
    def test_logger_name(self):
        """测试 logger 名称"""
        log_instance = Logger()
        
        assert log_instance.logger.name == "XingChen-V"
        
        print(f"✅ Logger 名称正确")
    
    def test_logger_has_handlers(self):
        """测试 logger 有处理器"""
        log_instance = Logger()
        
        # 应该有至少一个处理器（文件或控制台）
        assert len(log_instance.logger.handlers) > 0
        
        print(f"✅ Logger 处理器已添加")
    
    def test_log_directory_created(self):
        """测试日志目录被创建"""
        from xingchen.config.settings import settings
        
        assert os.path.exists(settings.LOG_DIR)
        
        print(f"✅ 日志目录已创建: {settings.LOG_DIR}")


class TestLoggerFunctionality:
    """测试日志功能"""
    
    def test_logger_info(self):
        """测试 info 级别日志"""
        # 使用全局 logger
        logger.info("测试 INFO 日志")
        
        # 验证日志文件存在
        from xingchen.config.settings import settings
        assert os.path.exists(settings.LOG_FILE)
        
        print(f"✅ INFO 日志记录成功")
    
    def test_logger_warning(self):
        """测试 warning 级别日志"""
        logger.warning("测试 WARNING 日志")
        
        from xingchen.config.settings import settings
        assert os.path.exists(settings.LOG_FILE)
        
        print(f"✅ WARNING 日志记录成功")
    
    def test_logger_error(self):
        """测试 error 级别日志"""
        logger.error("测试 ERROR 日志")
        
        from xingchen.config.settings import settings
        assert os.path.exists(settings.LOG_FILE)
        
        print(f"✅ ERROR 日志记录成功")
    
    def test_logger_debug(self):
        """测试 debug 级别日志"""
        logger.debug("测试 DEBUG 日志")
        
        from xingchen.config.settings import settings
        assert os.path.exists(settings.LOG_FILE)
        
        print(f"✅ DEBUG 日志记录成功")
