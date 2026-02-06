"""
测试 src/utils/logger.py
验证 Logger 功能：单例模式、文件处理、日志级别
"""

import pytest
import os
import logging
from pathlib import Path
from src.utils.logger import Logger, logger


class TestLoggerSingleton:
    """测试单例模式"""
    
    def test_logger_is_singleton(self):
        """测试 Logger 是单例"""
        logger1 = Logger()
        logger2 = Logger()
        
        assert logger1 is logger2
        assert id(logger1) == id(logger2)
        
        print(f"✓ Logger 单例模式正常")
    
    def test_logger_instance_has_logger_attribute(self):
        """测试 Logger 实例有 logger 属性"""
        log_instance = Logger()
        
        assert hasattr(log_instance, 'logger')
        assert isinstance(log_instance.logger, logging.Logger)
        
        print(f"✓ Logger 实例属性正常")


class TestLoggerInitialization:
    """测试初始化"""
    
    def test_logger_name(self):
        """测试 logger 名称"""
        log_instance = Logger()
        
        assert log_instance.logger.name == "XingChen-V"
        
        print(f"✓ Logger 名称正确")
    
    def test_logger_has_handlers(self):
        """测试 logger 有处理器"""
        log_instance = Logger()
        
        # 应该有至少一个处理器（文件或控制台）
        assert len(log_instance.logger.handlers) > 0
        
        print(f"✓ Logger 处理器已添加")
    
    def test_log_directory_created(self):
        """测试日志目录被创建"""
        from src.config.settings.settings import settings
        
        assert os.path.exists(settings.LOG_DIR)
        
        print(f"✓ 日志目录已创建: {settings.LOG_DIR}")


class TestLoggerFunctionality:
    """测试日志功能"""
    
    def test_logger_info(self):
        """测试 info 级别日志"""
        # 使用全局 logger
        logger.info("测试 INFO 日志")
        
        # 验证日志文件存在
        from src.config.settings.settings import settings
        assert os.path.exists(settings.LOG_FILE)
        
        print(f"✓ INFO 日志记录成功")
    
    def test_logger_warning(self):
        """测试 warning 级别日志"""
        logger.warning("测试 WARNING 日志")
        
        from src.config.settings.settings import settings
        assert os.path.exists(settings.LOG_FILE)
        
        print(f"✓ WARNING 日志记录成功")
    
    def test_logger_error(self):
        """测试 error 级别日志"""
        logger.error("测试 ERROR 日志")
        
        from src.config.settings.settings import settings
        assert os.path.exists(settings.LOG_FILE)
        
        print(f"✓ ERROR 日志记录成功")
    
    def test_logger_debug(self):
        """测试 debug 级别日志"""
        logger.debug("测试 DEBUG 日志")
        
        # DEBUG 可能不会被记录，取决于配置
        # 只验证不会抛出异常
        
        print(f"✓ DEBUG 日志调用成功")


class TestLoggerFileHandling:
    """测试文件处理"""
    
    def test_log_file_exists(self):
        """测试日志文件存在"""
        from src.config.settings.settings import settings
        
        # 记录一条日志确保文件被创建
        logger.info("测试日志文件创建")
        
        assert os.path.exists(settings.LOG_FILE)
        assert os.path.isfile(settings.LOG_FILE)
        
        print(f"✓ 日志文件存在: {settings.LOG_FILE}")
    
    def test_log_file_has_content(self):
        """测试日志文件有内容"""
        from src.config.settings.settings import settings
        
        # 记录一条唯一的日志
        unique_msg = "唯一测试消息_12345"
        logger.info(unique_msg)
        
        # 读取日志文件
        with open(settings.LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert unique_msg in content
        
        print(f"✓ 日志内容写入成功")
    
    def test_log_format(self):
        """测试日志格式"""
        from src.config.settings.settings import settings
        
        # 记录一条日志
        test_msg = "格式测试消息"
        logger.info(test_msg)
        
        # 读取最后一行
        with open(settings.LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 找到包含测试消息的行
        matching_lines = [line for line in lines if test_msg in line]
        assert len(matching_lines) > 0
        
        last_line = matching_lines[-1]
        
        # 验证格式包含时间戳、logger名称、级别
        assert "XingChen-V" in last_line
        assert "INFO" in last_line or "WARNING" in last_line or "ERROR" in last_line
        
        print(f"✓ 日志格式正确")


class TestLoggerEdgeCases:
    """测试边界情况"""
    
    def test_logger_with_chinese(self):
        """测试中文日志"""
        logger.info("这是一条中文日志消息：你好世界！")
        
        from src.config.settings.settings import settings
        with open(settings.LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "你好世界" in content
        
        print(f"✓ 中文日志记录成功")
    
    def test_logger_with_special_characters(self):
        """测试特殊字符日志"""
        logger.info("特殊字符: @#$%^&*()_+-=[]{}|;':\",./<>?")
        
        # 只验证不会抛出异常
        print(f"✓ 特殊字符日志记录成功")
    
    def test_logger_with_long_message(self):
        """测试长消息"""
        long_msg = "长消息测试 " * 100
        logger.info(long_msg)
        
        # 只验证不会抛出异常
        print(f"✓ 长消息日志记录成功")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
