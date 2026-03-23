"""
测试 xingchen/memory/wal.py
验证 WAL 功能：写入、重放、清空、崩溃恢复
"""

import pytest
import os
import json
import time
from pathlib import Path
from xingchen.memory.wal import WriteAheadLog


class TestWALBasicOperations:
    """测试 WAL 基础操作"""
    
    def test_wal_init(self, clean_wal):
        """测试 WAL 初始化"""
        wal = clean_wal
        assert wal is not None
        assert os.path.exists(wal.log_path)
        print(f"✅ WAL 初始化成功，路径: {wal.log_path}")
    
    def test_wal_append(self, clean_wal):
        """测试 WAL 追加操作"""
        wal = clean_wal
        
        # 追加一条操作
        wal.append("add_short_term", {"role": "user", "content": "测试消息"})
        
        # 验证文件存在且有内容
        assert os.path.exists(wal.log_path)
        with open(wal.log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["operation"] == "add_short_term"
        assert entry["data"]["content"] == "测试消息"
        
        print(f"✅ WAL 追加成功")
    
    def test_wal_append_multiple(self, clean_wal):
        """测试 WAL 追加多条操作"""
        wal = clean_wal
        
        # 追加多条
        for i in range(5):
            wal.append("add_short_term", {"role": "user", "content": f"消息{i}"})
        
        # 验证
        with open(wal.log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 5
        print(f"✅ WAL 追加 5 条成功")
    
    def test_wal_replay(self, clean_wal):
        """测试 WAL 重放"""
        wal = clean_wal
        
        # 写入数据
        test_data = [
            ("add_short_term", {"role": "user", "content": "消息1"}),
            ("add_short_term", {"role": "assistant", "content": "回复1"}),
            ("add_long_term", {"content": "重要事实", "category": "fact"}),
        ]
        
        for op, data in test_data:
            wal.append(op, data)
        
        # 重放
        entries = wal.replay()
        
        assert len(entries) == 3
        assert entries[0]["operation"] == "add_short_term"
        assert entries[1]["data"]["content"] == "回复1"
        assert entries[2]["operation"] == "add_long_term"
        
        print(f"✅ WAL 重放 {len(entries)} 条成功")
    
    def test_wal_clear(self, clean_wal):
        """测试 WAL 清空"""
        wal = clean_wal
        
        # 写入数据
        wal.append("add_short_term", {"role": "user", "content": "测试"})
        wal.append("add_short_term", {"role": "user", "content": "测试2"})
        
        # 清空
        wal.clear()
        
        # 验证文件为空
        with open(wal.log_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        assert content == ""
        print(f"✅ WAL 清空成功")
    
    def test_wal_get_entry_count(self, clean_wal):
        """测试 WAL 条目计数"""
        wal = clean_wal
        
        # 写入数据
        wal.append("add_short_term", {"role": "user", "content": "测试"})
        wal.append("add_short_term", {"role": "user", "content": "测试2"})
        
        # 验证
        assert wal.get_entry_count() == 2
        print(f"✅ WAL 计数成功")
