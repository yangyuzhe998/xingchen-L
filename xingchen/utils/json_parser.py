import json
import re
from typing import Any, Dict, Optional, Union, List

def extract_json(text: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """
    鲁棒地从字符串中提取 JSON 对象或数组。
    能够处理 Markdown 代码块和周围的干扰文本。
    通过括号计数法解决嵌套和贪婪匹配问题。
    """
    if not text:
        return None

    # 1. 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. 尝试清理 markdown 代码块
    # 移除 ```json ... ``` 或 ``` ... ```
    cleaned_text = re.sub(r'```(?:json)?\s*([\s\S]*?)\s*```', r'\1', text)
    try:
        return json.loads(cleaned_text.strip())
    except json.JSONDecodeError:
        pass
    
    # 3. 括号计数法提取
    # 查找所有可能的起始位置 { 或 [
    for i, char in enumerate(text):
        if char not in ('{', '['):
            continue
            
        start_char = char
        end_char = '}' if char == '{' else ']'
        
        stack = 0
        in_string = False
        escape = False
        
        for j in range(i, len(text)):
            curr = text[j]
            
            # 处理转义
            if escape:
                escape = False
                continue
            if curr == '\\':
                escape = True
                continue
                
            # 处理字符串内部（忽略字符串内的括号）
            if curr == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
                
            # 计数括号
            if curr == start_char:
                stack += 1
            elif curr == end_char:
                stack -= 1
                if stack == 0:
                    # 尝试解析提取到的片段
                    candidate = text[i:j+1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        # 解析失败，继续寻找下一个可能的闭合
                        break 
        
    return None
