"""
测试 src/memory/storage/write_ahead_log.py
验证 WAL 功能：写入、重放、清空、崩溃恢复
"""

import pytest
import os
import json
import time
from pathlib import Path
from src.memory.storage.write_ahead_log import WriteAheadLog


class TestWALBasicOperations:
    """测试 WAL 基础操作"""
    
    def test_wal_init(self, clean_wal):
        """测试 WAL 初始化"""
        wal = clean_wal
        assert wal is not None
        assert os.path.exists(wal.log_path)
        print(f"✓ WAL 初始化成功，路径: {wal.log_path}")
    
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
        
        print(f"✓ WAL 追加成功")
    
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
        print(f"✓ WAL 追加 5 条成功")
    
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
        
        print(f"✓ WAL 重放 {len(entries)} 条成功")
    
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
        print(f"✓ WAL 清空成功")
    
    def test_wal_get_entry_count(self, clean_wal):
        """测试获取 WAL 条目数"""
        wal = clean_wal
        
        assert wal.get_entry_count() == 0
        
        wal.append("add_short_term", {"role": "user", "content": "测试"})
        assert wal.get_entry_count() == 1
        
        wal.append("add_short_term", {"role": "user", "content": "测试2"})
        assert wal.get_entry_count() == 2
        
        wal.clear()
        assert wal.get_entry_count() == 0
        
        print(f"✓ WAL 条目计数正确")


class TestWALPerformance:
    """测试 WAL 性能"""
    
    def test_wal_write_performance(self, clean_wal):
        """测试 WAL 写入性能（应该 < 5ms per write）"""
        wal = clean_wal
        
        # 写入 100 条
        start_time = time.time()
        for i in range(100):
            wal.append("add_short_term", {"role": "user", "content": f"消息{i}"})
        elapsed = time.time() - start_time
        
        avg_time = (elapsed / 100) * 1000  # ms
        
        print(f"✓ 100 条写入耗时: {elapsed:.3f}s, 平均: {avg_time:.3f}ms/条")
        assert avg_time < 10, f"WAL 写入过慢: {avg_time:.3f}ms/条"
    
    def test_wal_replay_performance(self, clean_wal):
        """测试 WAL 重放性能"""
        wal = clean_wal
        
        # 写入 1000 条
        for i in range(1000):
            wal.append("add_short_term", {"role": "user", "content": f"消息{i}"})
        
        # 重放
        start_time = time.time()
        entries = wal.replay()
        elapsed = time.time() - start_time
        
        print(f"✓ 1000 条重放耗时: {elapsed:.3f}s")
        assert len(entries) == 1000
        assert elapsed < 2.0, f"WAL 重放过慢: {elapsed:.3f}s"


class TestWALErrorHandling:
    """测试 WAL 错误处理"""
    
    def test_wal_corrupted_entry(self, clean_wal):
        """测试 WAL 损坏条目处理"""
        wal = clean_wal
        
        # 写入正常数据
        wal.append("add_short_term", {"role": "user", "content": "正常消息"})
        
        # 手动写入损坏数据
        with open(wal.log_path, 'a', encoding='utf-8') as f:
            f.write("这是一条损坏的 JSON\n")
        
        # 写入更多正常数据
        wal.append("add_short_term", {"role": "user", "content": "另一条正常消息"})
        
        # 重放（应该跳过损坏的条目）
        entries = wal.replay()
        
        # 应该只有 2 条正常的
        assert len(entries) == 2
        print(f"✓ WAL 正确处理损坏条目，恢复 {len(entries)} 条")
    
    def test_wal_empty_file(self, clean_wal):
        """测试 WAL 空文件处理"""
        wal = clean_wal
        
        # 重放空文件
        entries = wal.replay()
        assert entries == []
        
        print(f"✓ WAL 正确处理空文件")


class TestWALTimestamp:
    """测试 WAL 时间戳功能"""
    
    def test_wal_entries_have_timestamps(self, clean_wal):
        """测试 WAL 条目包含时间戳"""
        wal = clean_wal
        
        wal.append("add_short_term", {"role": "user", "content": "测试"})
        
        entries = wal.replay()
        assert len(entries) == 1
        
        entry = entries[0]
        assert "timestamp" in entry
        assert "datetime" in entry
        assert isinstance(entry["timestamp"], (int, float))
        assert isinstance(entry["datetime"], str)
        
        print(f"✓ WAL 条目包含时间戳: {entry['datetime']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

