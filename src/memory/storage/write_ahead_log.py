"""
Write-Ahead Log (WAL) 实现
用于防止系统崩溃时的数据丢失
"""

import json
import os
import time
from typing import Dict, Any, List
from datetime import datetime
from src.utils.logger import logger


class WriteAheadLog:
    """
    写前日志 (Write-Ahead Log)
    
    功能：
    1. 每次操作先写入 WAL，再执行实际操作
    2. 系统启动时重放 WAL，恢复未提交的数据
    3. 成功 checkpoint 后清空 WAL
    """
    
    def __init__(self, log_path: str = "memory_data/wal.log"):
        self.log_path = log_path
        self._ensure_log_exists()
        logger.info(f"[WAL] 初始化完成，日志路径: {log_path}")
    
    def _ensure_log_exists(self):
        """确保日志文件和目录存在"""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            open(self.log_path, 'w').close()
    
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
            logger.info("[WAL] 日志已清空")
        except Exception as e:
            logger.error(f"[WAL] 清空失败: {e}", exc_info=True)
    
    def checkpoint(self):
        """
        执行 checkpoint：备份当前 WAL，然后清空
        用于调试和审计
        """
        try:
            if os.path.exists(self.log_path) and os.path.getsize(self.log_path) > 0:
                # 备份到带时间戳的文件
                backup_path = f"{self.log_path}.{int(time.time())}.bak"
                with open(self.log_path, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                logger.info(f"[WAL] 已备份到: {backup_path}")
            
            self.clear()
        except Exception as e:
            logger.error(f"[WAL] Checkpoint 失败: {e}", exc_info=True)
    
    def get_size(self) -> int:
        """获取 WAL 文件大小（字节）"""
        try:
            return os.path.getsize(self.log_path)
        except:
            return 0
    
    def get_entry_count(self) -> int:
        """获取 WAL 中的条目数量"""
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                return sum(1 for line in f if line.strip())
        except:
            return 0

    def should_checkpoint(self, threshold: int = 1000) -> bool:
        '''判断是否需要 checkpoint'''
        return self.get_entry_count() >= threshold
    
    def verify(self) -> tuple:
        '''验证 WAL 完整性'''
        corrupted_lines = []
        if not os.path.exists(self.log_path):
            return True, []
        with open(self.log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line.strip())
                    if 'operation' not in entry or 'data' not in entry:
                        corrupted_lines.append(i)
                except json.JSONDecodeError:
                    corrupted_lines.append(i)
        is_valid = len(corrupted_lines) == 0
        if not is_valid:
            logger.warning(f'[WAL] 发现 {len(corrupted_lines)} 条损坏记录')
        return is_valid, corrupted_lines
    
    def repair(self) -> int:
        '''修复损坏的 WAL'''
        if not os.path.exists(self.log_path):
            return 0
        valid_entries = []
        corrupted_count = 0
        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line.strip())
                    if 'operation' in entry and 'data' in entry:
                        valid_entries.append(entry)
                    else:
                        corrupted_count += 1
                except json.JSONDecodeError:
                    corrupted_count += 1
        with open(self.log_path, 'w', encoding='utf-8') as f:
            for entry in valid_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        if corrupted_count > 0:
            logger.info(f'[WAL] 修复完成：移除了 {corrupted_count} 条损坏记录')
        return corrupted_count
