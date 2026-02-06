"""
测试 src/config/prompts/prompts.py
验证 Prompt 模板定义
"""

import pytest
from src.config.prompts.prompts import (
    DRIVER_SYSTEM_PROMPT,
    NAVIGATOR_SYSTEM_PROMPT,
    PROACTIVE_DRIVER_PROMPT,
    NAVIGATOR_USER_PROMPT,
    COGNITIVE_GRAPH_PROMPT,
    DIARY_GENERATION_PROMPT,
    FACT_EXTRACTION_PROMPT,
    ALIAS_EXTRACTION_PROMPT,
    MEMORY_SUMMARY_PROMPT,
    TOOL_CN_NAME_MAP
)


class TestPromptTemplates:
    """测试 Prompt 模板定义"""
    
    def test_driver_system_prompt_exists(self):
        """测试 Driver 系统 Prompt 存在且非空"""
        assert DRIVER_SYSTEM_PROMPT
        assert len(DRIVER_SYSTEM_PROMPT) > 100
        assert "星辰" in DRIVER_SYSTEM_PROMPT or "独立数字生命" in DRIVER_SYSTEM_PROMPT
        print(f"✓ DRIVER_SYSTEM_PROMPT 长度: {len(DRIVER_SYSTEM_PROMPT)} 字符")
    
    def test_navigator_system_prompt_exists(self):
        """测试 Navigator 系统 Prompt 存在且非空"""
        assert NAVIGATOR_SYSTEM_PROMPT
        assert len(NAVIGATOR_SYSTEM_PROMPT) > 100
        assert "潜意识" in NAVIGATOR_SYSTEM_PROMPT or "S脑" in NAVIGATOR_SYSTEM_PROMPT
        print(f"✓ NAVIGATOR_SYSTEM_PROMPT 长度: {len(NAVIGATOR_SYSTEM_PROMPT)} 字符")
    
    def test_proactive_driver_prompt_exists(self):
        """测试主动对话 Prompt 存在"""
        assert PROACTIVE_DRIVER_PROMPT
        assert "主动" in PROACTIVE_DRIVER_PROMPT or "沉默" in PROACTIVE_DRIVER_PROMPT
        print(f"✓ PROACTIVE_DRIVER_PROMPT 长度: {len(PROACTIVE_DRIVER_PROMPT)} 字符")
    
    def test_navigator_user_prompt_exists(self):
        """测试 Navigator 用户 Prompt 存在"""
        assert NAVIGATOR_USER_PROMPT
        assert "交互日志" in NAVIGATOR_USER_PROMPT or "Cycle Log" in NAVIGATOR_USER_PROMPT
        print(f"✓ NAVIGATOR_USER_PROMPT 长度: {len(NAVIGATOR_USER_PROMPT)} 字符")
    
    def test_cognitive_graph_prompt_exists(self):
        """测试认知图谱 Prompt 存在"""
        assert COGNITIVE_GRAPH_PROMPT
        assert "认知图谱" in COGNITIVE_GRAPH_PROMPT or "实体" in COGNITIVE_GRAPH_PROMPT
        print(f"✓ COGNITIVE_GRAPH_PROMPT 长度: {len(COGNITIVE_GRAPH_PROMPT)} 字符")
    
    def test_diary_generation_prompt_exists(self):
        """测试日记生成 Prompt 存在"""
        assert DIARY_GENERATION_PROMPT
        assert "日记" in DIARY_GENERATION_PROMPT
        print(f"✓ DIARY_GENERATION_PROMPT 长度: {len(DIARY_GENERATION_PROMPT)} 字符")
    
    def test_fact_extraction_prompt_exists(self):
        """测试事实提取 Prompt 存在"""
        assert FACT_EXTRACTION_PROMPT
        assert "事实" in FACT_EXTRACTION_PROMPT
        print(f"✓ FACT_EXTRACTION_PROMPT 长度: {len(FACT_EXTRACTION_PROMPT)} 字符")
    
    def test_alias_extraction_prompt_exists(self):
        """测试别名提取 Prompt 存在"""
        assert ALIAS_EXTRACTION_PROMPT
        assert "别名" in ALIAS_EXTRACTION_PROMPT or "昵称" in ALIAS_EXTRACTION_PROMPT
        print(f"✓ ALIAS_EXTRACTION_PROMPT 长度: {len(ALIAS_EXTRACTION_PROMPT)} 字符")
    
    def test_memory_summary_prompt_exists(self):
        """测试记忆总结 Prompt 存在"""
        assert MEMORY_SUMMARY_PROMPT
        assert "记忆" in MEMORY_SUMMARY_PROMPT or "整合" in MEMORY_SUMMARY_PROMPT
        print(f"✓ MEMORY_SUMMARY_PROMPT 长度: {len(MEMORY_SUMMARY_PROMPT)} 字符")


class TestPromptTemplateVariables:
    """测试 Prompt 模板变量"""
    
    def test_driver_prompt_has_variables(self):
        """测试 Driver Prompt 包含必要的变量占位符"""
        required_vars = [
            "{current_time}",
            "{psyche_desc}",
            "{suggestion}",
            "{long_term_context}"
        ]
        
        for var in required_vars:
            assert var in DRIVER_SYSTEM_PROMPT, f"缺少变量: {var}"
        
        print(f"✓ Driver Prompt 包含所有必要变量")
    
    def test_navigator_prompt_has_variables(self):
        """测试 Navigator Prompt 包含必要的变量占位符"""
        required_vars = [
            "{project_context}"
        ]
        
        for var in required_vars:
            assert var in NAVIGATOR_SYSTEM_PROMPT, f"缺少变量: {var}"
        
        print(f"✓ Navigator Prompt 包含所有必要变量")
    
    def test_navigator_user_prompt_has_variables(self):
        """测试 Navigator User Prompt 包含必要的变量"""
        required_vars = [
            "{long_term_context}",
            "{script}"
        ]
        
        for var in required_vars:
            assert var in NAVIGATOR_USER_PROMPT, f"缺少变量: {var}"
        
        print(f"✓ Navigator User Prompt 包含所有必要变量")


class TestToolNameMapping:
    """测试工具名称映射"""
    
    def test_tool_cn_name_map_exists(self):
        """测试工具中文名称映射表存在"""
        assert TOOL_CN_NAME_MAP
        assert isinstance(TOOL_CN_NAME_MAP, dict)
        print(f"✓ TOOL_CN_NAME_MAP 包含 {len(TOOL_CN_NAME_MAP)} 个工具映射")
    
    def test_tool_names_have_emojis(self):
        """测试工具名称包含 emoji（提升用户体验）"""
        for tool_id, cn_name in TOOL_CN_NAME_MAP.items():
            # 检查是否包含 emoji（简单检查：是否包含非 ASCII 字符）
            has_emoji = any(ord(char) > 127 for char in cn_name)
            assert has_emoji, f"{tool_id} 的中文名称应该包含 emoji"
        
        print(f"✓ 所有工具名称都包含 emoji")


class TestPromptQuality:
    """测试 Prompt 质量"""
    
    def test_prompts_support_chinese(self):
        """测试所有 Prompt 都支持中文"""
        prompts = [
            DRIVER_SYSTEM_PROMPT,
            NAVIGATOR_SYSTEM_PROMPT,
            PROACTIVE_DRIVER_PROMPT,
            NAVIGATOR_USER_PROMPT,
            COGNITIVE_GRAPH_PROMPT,
            DIARY_GENERATION_PROMPT,
            FACT_EXTRACTION_PROMPT,
            ALIAS_EXTRACTION_PROMPT,
            MEMORY_SUMMARY_PROMPT
        ]
        
        for prompt in prompts:
            # 检查是否包含中文字符
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in prompt)
            assert has_chinese, "Prompt 应该包含中文"
        
        print("✓ 所有 Prompt 都支持中文")
    
    def test_driver_prompt_emphasizes_independence(self):
        """测试 Driver Prompt 强调独立性"""
        keywords = ["独立", "意志", "情感", "价值观", "平等"]
        found = sum(1 for keyword in keywords if keyword in DRIVER_SYSTEM_PROMPT)
        
        assert found >= 3, "Driver Prompt 应该强调独立性和情感"
        print(f"✓ Driver Prompt 强调独立性（找到 {found} 个关键词）")
    
    def test_navigator_prompt_emphasizes_intuition(self):
        """测试 Navigator Prompt 强调直觉和潜意识"""
        keywords = ["直觉", "潜意识", "本能", "联想", "梦境"]
        found = sum(1 for keyword in keywords if keyword in NAVIGATOR_SYSTEM_PROMPT)
        
        assert found >= 3, "Navigator Prompt 应该强调直觉和潜意识"
        print(f"✓ Navigator Prompt 强调直觉（找到 {found} 个关键词）")
    
    def test_prompts_length_reasonable(self):
        """测试 Prompt 长度合理"""
        # 主要的 Prompt 不应该超过 5000 字符
        assert len(DRIVER_SYSTEM_PROMPT) < 5000, "Driver Prompt 过长"
        assert len(NAVIGATOR_SYSTEM_PROMPT) < 5000, "Navigator Prompt 过长"
        
        print(f"✓ Prompt 长度合理")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
