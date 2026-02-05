
import json
import re
from typing import Any, Dict, Optional, Union, List

def extract_json(text: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """
    鲁棒地从字符串中提取 JSON 对象或数组。
    能够处理 Markdown 代码块和周围的干扰文本。
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
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        pass
    
    # 3. 正则搜索第一个有效的 JSON 对象 {...} 或数组 [...]
    # 注意: 这是一个简单的递归匹配模拟
    try:
        # 查找对象或数组的开始
        match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
        if match:
            candidate = match.group(1)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # 如果简单的正则失败，可能是因为嵌套括号问题。
                # 暂时返回 None，或者如果需要可以尝试更复杂的解析。
                pass
    except Exception:
        pass
        
    return None
