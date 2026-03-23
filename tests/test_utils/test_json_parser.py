"""
测试 xingchen/utils/json_parser.py
验证 JSON 提取功能：直接解析、Markdown 清理、正则搜索
"""

import pytest
from xingchen.utils.json_parser import extract_json


class TestJsonParserBasic:
    """测试基础 JSON 解析"""
    
    def test_extract_valid_json_object(self):
        """测试提取有效的 JSON 对象"""
        text = '{"name": "张三", "age": 25}'
        result = extract_json(text)
        
        assert result is not None
        assert isinstance(result, dict)
        assert result["name"] == "张三"
        assert result["age"] == 25
        
        print(f"✅ 有效 JSON 对象提取成功")
    
    def test_extract_valid_json_array(self):
        """测试提取有效的 JSON 数组"""
        text = '[1, 2, 3, 4, 5]'
        result = extract_json(text)
        
        assert result is not None
        assert isinstance(result, list)
        assert result == [1, 2, 3, 4, 5]
        
        print(f"✅ 有效 JSON 数组提取成功")
    
    def test_extract_nested_json(self):
        """测试提取嵌套 JSON"""
        text = '{"user": {"name": "李四", "profile": {"age": 30, "city": "北京"}}}'
        result = extract_json(text)
        
        assert result is not None
        assert result["user"]["name"] == "李四"
        assert result["user"]["profile"]["age"] == 30
        assert result["user"]["profile"]["city"] == "北京"
        
        print(f"✅ 嵌套 JSON 提取成功")
    
    def test_extract_empty_string(self):
        """测试空字符串"""
        result = extract_json("")
        assert result is None
        
        print(f"✅ 空字符串处理正确")
    
    def test_extract_none(self):
        """测试 None 输入"""
        result = extract_json(None)
        assert result is None
        
        print(f"✅ None 输入处理正确")


class TestJsonParserMarkdown:
    """测试 Markdown 代码块处理"""
    
    def test_extract_from_markdown_json_block(self):
        """测试从 ```json 代码块提取"""
        text = '''
这是一些说明文字
```json
{
    "name": "王五",
    "age": 28
}
```
更多文字
'''
        result = extract_json(text)
        
        assert result is not None
        assert isinstance(result, dict)
        assert result["name"] == "王五"
        assert result["age"] == 28
        
        print(f"✅ Markdown json 代码块提取成功")
    
    def test_extract_from_markdown_generic_block(self):
        """测试从 ``` 通用代码块提取"""
        text = '''
```
{"status": "success", "code": 200}
```
'''
        result = extract_json(text)
        
        assert result is not None
        assert result["status"] == "success"
        assert result["code"] == 200
        
        print(f"✅ Markdown 通用代码块提取成功")
