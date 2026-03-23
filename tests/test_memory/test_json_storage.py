"""
测试 xingchen/memory/storage/local.py (JsonStorage)
验证 JSON 存储功能：保存、加载、错误处理
"""

import pytest
import os
import json
from pathlib import Path
from xingchen.memory.storage.local import JsonStorage


class TestJsonStorageBasic:
    """测试 JsonStorage 基础操作"""
    
    def test_json_storage_init(self, clean_memory_data):
        """测试 JsonStorage 初始化"""
        # 使用 fixture 返回的临时目录
        storage_path = clean_memory_data / "test_storage_init.json"
        storage = JsonStorage(str(storage_path))
        
        assert storage is not None
        assert storage.file_path == str(storage_path)
        print(f"✅ JsonStorage 初始化成功，路径: {storage.file_path}")
    
    def test_json_storage_save_and_load(self, clean_memory_data):
        """测试保存和加载"""
        storage_path = clean_memory_data / "test_storage_save.json"
        storage = JsonStorage(str(storage_path))
        
        # 测试数据
        test_data = {
            "facts": ["用户喜欢编程", "用户住在北京"],
            "count": 2,
            "metadata": {"version": "1.0"}
        }
        
        # 保存
        storage.save(test_data)
        assert os.path.exists(storage_path)
        print(f"✅ 数据已保存到 {storage_path}")
        
        # 加载
        loaded_data = storage.load()
        # JsonStorage 总是返回列表
        assert isinstance(loaded_data, list)
        assert len(loaded_data) == 1
        assert loaded_data[0] == test_data
        assert loaded_data[0]["count"] == 2
        assert len(loaded_data[0]["facts"]) == 2
        print(f"✅ 数据加载成功")
    
    def test_json_storage_load_nonexistent(self, clean_memory_data):
        """测试加载不存在的文件"""
        storage_path = clean_memory_data / "nonexistent.json"
        storage = JsonStorage(str(storage_path))
        
        # 加载不存在的文件应该返回空列表
        loaded_data = storage.load()
        assert loaded_data == []
        print(f"✅ 不存在的文件返回空列表")
    
    def test_json_storage_overwrite(self, clean_memory_data):
        """测试覆盖写入"""
        storage_path = clean_memory_data / "test_storage_overwrite.json"
        storage = JsonStorage(str(storage_path))
        
        # 第一次保存
        data1 = {"value": 1}
        storage.save(data1)
        
        # 第二次保存（覆盖）
        data2 = {"value": 2, "new_field": "test"}
        storage.save(data2)
        
        # 验证
        loaded = storage.load()
        assert loaded[0] == data2
        assert loaded[0]["value"] == 2
        assert "new_field" in loaded[0]
        print(f"✅ 覆盖写入成功")
    
    def test_json_storage_empty_data(self, clean_memory_data):
        """测试保存空数据"""
        storage_path = clean_memory_data / "test_storage_empty.json"
        storage = JsonStorage(str(storage_path))
        
        # 保存空列表
        storage.save([])
        
        # 加载
        loaded = storage.load()
        assert loaded == []
        print(f"✅ 空数据保存和加载正常")


class TestJsonStorageDataTypes:
    """测试 JsonStorage 支持的数据类型"""
    
    def test_json_storage_nested_data(self, clean_memory_data):
        """测试嵌套数据"""
        storage_path = clean_memory_data / "test_storage_nested.json"
        storage = JsonStorage(str(storage_path))
        
        nested_data = {
            "a": 1,
            "b": [1, 2, {"c": 3}],
            "d": {"e": {"f": 4}}
        }
        
        storage.save(nested_data)
        loaded = storage.load()
        assert loaded[0] == nested_data
        print(f"✅ 嵌套数据保存和加载正常")
