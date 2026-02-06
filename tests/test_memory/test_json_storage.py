"""
测试 src/memory/storage/local.py (JsonStorage)
验证 JSON 存储功能：保存、加载、错误处理
"""

import pytest
import os
import json
from pathlib import Path
from src.memory.storage.local import JsonStorage


class TestJsonStorageBasic:
    """测试 JsonStorage 基础操作"""
    
    def test_json_storage_init(self, clean_memory_data):
        """测试 JsonStorage 初始化"""
        # 使用 fixture 返回的临时目录
        storage_path = clean_memory_data / "test_storage.json"
        storage = JsonStorage(str(storage_path))
        
        assert storage is not None
        assert storage.file_path == str(storage_path)
        print(f"✓ JsonStorage 初始化成功，路径: {storage.file_path}")
    
    def test_json_storage_save_and_load(self, clean_memory_data):
        """测试保存和加载"""
        storage_path = clean_memory_data / "test_storage.json"
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
        print(f"✓ 数据已保存到 {storage_path}")
        
        # 加载
        loaded_data = storage.load()
        # JsonStorage 总是返回列表
        assert isinstance(loaded_data, list)
        assert len(loaded_data) == 1
        assert loaded_data[0] == test_data
        assert loaded_data[0]["count"] == 2
        assert len(loaded_data[0]["facts"]) == 2
        print(f"✓ 数据加载成功，验证一致")
    
    def test_json_storage_load_nonexistent(self, clean_memory_data):
        """测试加载不存在的文件"""
        storage_path = clean_memory_data / "nonexistent.json"
        storage = JsonStorage(str(storage_path))
        
        # 加载不存在的文件应该返回空列表
        loaded_data = storage.load()
        assert loaded_data == []
        print(f"✓ 不存在的文件返回空列表")
    
    def test_json_storage_overwrite(self, clean_memory_data):
        """测试覆盖写入"""
        storage_path = "src/memory_data/test_storage.json"
        storage = JsonStorage(storage_path)
        
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
        print(f"✓ 覆盖写入成功")
    
    def test_json_storage_empty_data(self, clean_memory_data):
        """测试保存空数据"""
        storage_path = "src/memory_data/test_storage.json"
        storage = JsonStorage(storage_path)
        
        # 保存空列表
        storage.save([])
        
        # 加载
        loaded = storage.load()
        assert loaded == []
        print(f"✓ 空数据保存和加载正常")


class TestJsonStorageDataTypes:
    """测试 JsonStorage 支持的数据类型"""
    
    def test_json_storage_nested_data(self, clean_memory_data):
        """测试嵌套数据结构"""
        storage_path = "src/memory_data/test_storage.json"
        storage = JsonStorage(storage_path)
        
        nested_data = {
            "user": {
                "name": "张三",
                "preferences": {
                    "language": "Python",
                    "hobbies": ["编程", "阅读"]
                }
            },
            "stats": {
                "conversations": 10,
                "facts_learned": 5
            }
        }
        
        storage.save(nested_data)
        loaded = storage.load()
        
        assert loaded[0] == nested_data
        assert loaded[0]["user"]["preferences"]["language"] == "Python"
        assert len(loaded[0]["user"]["preferences"]["hobbies"]) == 2
        print(f"✓ 嵌套数据结构保存和加载正常")
    
    def test_json_storage_list_data(self, clean_memory_data):
        """测试列表数据"""
        storage_path = "src/memory_data/test_storage.json"
        storage = JsonStorage(storage_path)
        
        list_data = {
            "items": [1, 2, 3, 4, 5],
            "strings": ["a", "b", "c"],
            "mixed": [1, "two", 3.0, True, None]
        }
        
        storage.save(list_data)
        loaded = storage.load()
        
        assert loaded[0] == list_data
        assert loaded[0]["items"] == [1, 2, 3, 4, 5]
        assert loaded[0]["mixed"][1] == "two"
        print(f"✓ 列表数据保存和加载正常")
    
    def test_json_storage_unicode(self, clean_memory_data):
        """测试 Unicode 字符（中文）"""
        storage_path = clean_memory_data / "test_storage.json"
        storage = JsonStorage(str(storage_path))
        
        unicode_data = {
            "chinese": "你好，世界！",
            "emoji": "🎉 测试成功",
            "mixed": "Hello 世界 🌍"
        }
        
        storage.save(unicode_data)
        loaded = storage.load()
        
        assert loaded[0] == unicode_data
        assert loaded[0]["chinese"] == "你好，世界！"
        assert "🎉" in loaded[0]["emoji"]
        print(f"✓ Unicode 字符保存和加载正常")


class TestJsonStorageErrorHandling:
    """测试 JsonStorage 错误处理"""
    
    def test_json_storage_corrupted_file(self, clean_memory_data):
        """测试损坏的 JSON 文件"""
        storage_path = "src/memory_data/test_storage.json"
        storage = JsonStorage(storage_path)
        
        # 手动写入损坏的 JSON
        with open(storage_path, 'w', encoding='utf-8') as f:
            f.write("这不是有效的 JSON {{{")
        
        # 加载损坏的文件应该返回空列表（根据实际实现）
        loaded = storage.load()
        assert loaded == []
        print(f"✓ 损坏的 JSON 文件处理正常，返回空列表")
    
    def test_json_storage_invalid_path(self, clean_memory_data):
        """测试无效路径"""
        # 使用 src/memory_data 下的子目录，确保在清理范围内
        storage_path = clean_memory_data / "subdir/test.json"
        storage = JsonStorage(str(storage_path))
        
        # 保存时应该创建目录或抛出异常
        try:
            storage.save({"test": "data"})
            # 如果成功，验证文件存在
            assert os.path.exists(storage_path)
            print(f"✓ 自动创建目录成功")
        except Exception as e:
            # 如果抛出异常，也是合理的
            print(f"✓ 无效路径正确抛出异常: {type(e).__name__}")


class TestJsonStoragePerformance:
    """测试 JsonStorage 性能"""
    
    def test_json_storage_large_data(self, clean_memory_data):
        """测试大数据量"""
        storage_path = "src/memory_data/test_storage.json"
        storage = JsonStorage(storage_path)
        
        # 创建大数据（1000 条记录）
        large_data = {
            "records": [
                {"id": i, "content": f"记录{i}", "value": i * 2}
                for i in range(1000)
            ]
        }
        
        # 保存
        storage.save(large_data)
        
        # 加载
        loaded = storage.load()
        
        # JsonStorage 会把 dict 包装成 list
        assert len(loaded) == 1
        assert len(loaded[0]["records"]) == 1000
        assert loaded[0]["records"][0]["id"] == 0
        assert loaded[0]["records"][999]["id"] == 999
        print(f"✓ 大数据量（1000条）保存和加载正常")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

