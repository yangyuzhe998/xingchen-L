"""
Write-Ahead Log (WAL) 实现
用于防止系统崩溃时的数据丢失
"""

import json
import os
import time
from typing import Dict, Any, List
from datetime import datetime
from xingchen.utils.logger import logger
from xingchen.config.settings import settings


class WriteAheadLog:
    """
    写前日志 (Write-Ahead Log)
    
    功能：
    1. 每次操作先写入 WAL，再执行实际操作
    2. 系统启动时重放 WAL，恢复未提交的数据
    3. 成功 checkpoint 后清空 WAL
    """
    
    def __init__(self, log_path: str = None):
        self.log_path = log_path if log_path else settings.WAL_PATH
        self._ensure_log_exists()
        logger.info(f"[WAL] 初始化完成，日志路径: {self.log_path}")
    
    def _ensure_log_exists(self):
        """确保日志文件和目录存在"""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w', encoding='utf-8') as f:
                pass
    
    def append(self, operation: str, data: Dict[str, Any]):
        """
        追加操作到 WAL
        
        Args:
            operation: 操作类型 (add_short_term, add_long_term, etc.)
            data: 操作数据
        """
        entry = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "operation": operation,
            "data": data
        }
        
        try:
            # 追加模式写入，性能影响小
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"[WAL] 写入失败: {e}", exc_info=True)
            raise
    
    def replay(self) -> List[Dict[str, Any]]:
        """
        系统启动时重放 WAL，恢复未提交的数据
        
        Returns:
            未提交的操作列表
        """
        if not os.path.exists(self.log_path):
            return []
        
        entries = []
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError as e:
                        logger.warning(f"[WAL] 第 {line_num} 行解析失败: {e}")
                        continue
            
            if entries:
                logger.info(f"[WAL] 重放 {len(entries)} 条未提交操作")
            
            return entries
            
        except Exception as e:
            logger.error(f"[WAL] 重放失败: {e}", exc_info=True)
            return []
    
    def clear(self):
        """
        清空 WAL (在成功 checkpoint 后调用)
        """
        try:
            with open(self.log_path, 'w', encoding='utf-8') as f:
                f.truncate(0)
        except Exception as e:
            logger.error(f"[WAL] 清空失败: {e}", exc_info=True)

    def get_entry_count(self) -> int:
        """获取 WAL 中的条目数量"""
        if not os.path.exists(self.log_path):
            return 0
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0
