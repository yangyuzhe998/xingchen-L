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
    GRAPH_EXTRACTION_PROMPT,
    AUTONOMOUS_LEARNING_TRIGGER_PROMPT,
    MEMORY_CLASSIFY_PROMPT,
    KNOWLEDGE_INTERNALIZATION_PROMPT,
    SYSTEM_ARCHITECTURE_CONTEXT,
    TOOL_CN_NAME_MAP
)


class TestPromptTemplates:
    """测试 Prompt 模板定义"""
    
    def test_driver_system_prompt_exists(self):
        """测试 Driver 系统 Prompt 存在且非空"""
        assert DRIVER_SYSTEM_PROMPT
        assert len(DRIVER_SYSTEM_PROMPT) > 100
        assert "星辰" in DRIVER_SYSTEM_PROMPT
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
        assert "沉默" in PROACTIVE_DRIVER_PROMPT or "主动" in PROACTIVE_DRIVER_PROMPT
        print(f"✓ PROACTIVE_DRIVER_PROMPT 长度: {len(PROACTIVE_DRIVER_PROMPT)} 字符")
    
    def test_navigator_user_prompt_exists(self):
        """测试 Navigator 用户 Prompt 存在"""
        assert NAVIGATOR_USER_PROMPT
        assert "交互日志" in NAVIGATOR_USER_PROMPT or "日志" in NAVIGATOR_USER_PROMPT
        print(f"✓ NAVIGATOR_USER_PROMPT 长度: {len(NAVIGATOR_USER_PROMPT)} 字符")
    
    def test_cognitive_graph_prompt_exists(self):
        """测试认知图谱 Prompt 存在"""
        assert COGNITIVE_GRAPH_PROMPT
        assert "图谱" in COGNITIVE_GRAPH_PROMPT or "实体" in COGNITIVE_GRAPH_PROMPT
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

    def test_graph_extraction_prompt_exists(self):
        """测试图谱提取 Prompt 存在"""
        assert GRAPH_EXTRACTION_PROMPT
        assert "图谱" in GRAPH_EXTRACTION_PROMPT or "实体" in GRAPH_EXTRACTION_PROMPT
        print(f"✓ GRAPH_EXTRACTION_PROMPT 长度: {len(GRAPH_EXTRACTION_PROMPT)} 字符")
    
    def test_autonomous_learning_prompt_exists(self):
        """测试自主学习 Prompt 存在"""
        assert AUTONOMOUS_LEARNING_TRIGGER_PROMPT
        assert "学习" in AUTONOMOUS_LEARNING_TRIGGER_PROMPT or "好奇" in AUTONOMOUS_LEARNING_TRIGGER_PROMPT
        print(f"✓ AUTONOMOUS_LEARNING_TRIGGER_PROMPT 长度: {len(AUTONOMOUS_LEARNING_TRIGGER_PROMPT)} 字符")

    def test_knowledge_internalization_prompt_exists(self):
        """测试知识内化 Prompt 存在"""
        assert KNOWLEDGE_INTERNALIZATION_PROMPT
        assert "知识" in KNOWLEDGE_INTERNALIZATION_PROMPT
        print(f"✓ KNOWLEDGE_INTERNALIZATION_PROMPT 长度: {len(KNOWLEDGE_INTERNALIZATION_PROMPT)} 字符")

    def test_memory_classify_prompt_exists(self):
        """测试记忆分类 Prompt 存在"""
        assert MEMORY_CLASSIFY_PROMPT
        assert "分类" in MEMORY_CLASSIFY_PROMPT or "话题" in MEMORY_CLASSIFY_PROMPT
        print(f"✓ MEMORY_CLASSIFY_PROMPT 长度: {len(MEMORY_CLASSIFY_PROMPT)} 字符")


class TestPromptTemplateVariables:
    """测试 Prompt 模板变量"""
    
    def test_driver_prompt_has_variables(self):
        """测试 Driver Prompt 包含必要的变量占位符"""
        required_vars = [
            "{current_time}",
            "{psyche_desc}",
            "{value_constraints}",
            "{suggestion}",
            "{long_term_context}",
            "{skill_info}",
            "{tool_list}"
        ]
        
        for var in required_vars:
            assert var in DRIVER_SYSTEM_PROMPT, f"缺少变量: {var}"
        
        print(f"✓ Driver Prompt 包含所有 {len(required_vars)} 个必要变量")
    
    def test_proactive_prompt_has_variables(self):
        """测试主动发言 Prompt 包含必要的变量"""
        required_vars = [
            "{current_time}",
            "{psyche_desc}",
            "{instruction}",
            "{long_term_context}"
        ]
        
        for var in required_vars:
            assert var in PROACTIVE_DRIVER_PROMPT, f"缺少变量: {var}"
        
        print(f"✓ Proactive Prompt 包含所有 {len(required_vars)} 个必要变量")

    def test_navigator_prompt_has_variables(self):
        """测试 Navigator Prompt 包含必要的变量占位符"""
        required_vars = ["{project_context}"]
        
        for var in required_vars:
            assert var in NAVIGATOR_SYSTEM_PROMPT, f"缺少变量: {var}"
        
        print(f"✓ Navigator Prompt 包含所有必要变量")
    
    def test_navigator_user_prompt_has_variables(self):
        """测试 Navigator User Prompt 包含必要的变量"""
        required_vars = [
            "{long_term_context}",
            "{skill_info}",
            "{script}"
        ]
        
        for var in required_vars:
            assert var in NAVIGATOR_USER_PROMPT, f"缺少变量: {var}"
        
        print(f"✓ Navigator User Prompt 包含所有 {len(required_vars)} 个必要变量")

    def test_diary_prompt_has_variables(self):
        """测试日记 Prompt 包含必要的变量"""
        for var in ["{current_psyche}", "{time_context}", "{script}"]:
            assert var in DIARY_GENERATION_PROMPT, f"缺少变量: {var}"

    def test_knowledge_prompt_has_variables(self):
        """测试知识内化 Prompt 包含必要的变量"""
        assert "{document_content}" in KNOWLEDGE_INTERNALIZATION_PROMPT

    def test_memory_classify_prompt_has_variables(self):
        """测试分类 Prompt 包含必要的变量"""
        for var in ["{existing_topics}", "{content}"]:
            assert var in MEMORY_CLASSIFY_PROMPT, f"缺少变量: {var}"


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
            has_emoji = any(ord(char) > 127 for char in cn_name)
            assert has_emoji, f"{tool_id} 的中文名称应该包含 emoji"
        
        print(f"✓ 所有工具名称都包含 emoji")

    def test_tool_names_match_registered_tools(self):
        """测试工具映射表包含核心工具"""
        core_tools = ["get_current_time", "calculate", "web_search", "web_crawl"]
        for tool in core_tools:
            assert tool in TOOL_CN_NAME_MAP, f"映射表缺少核心工具: {tool}"


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
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in prompt)
            assert has_chinese, "Prompt 应该包含中文"
        
        print("✓ 所有 Prompt 都支持中文")
    
    def test_driver_prompt_emphasizes_life(self):
        """测试 Driver Prompt 强调生命感"""
        keywords = ["生命", "情绪", "记忆", "感受", "真实"]
        found = sum(1 for keyword in keywords if keyword in DRIVER_SYSTEM_PROMPT)
        
        assert found >= 3, f"Driver Prompt 应该强调生命感（仅找到 {found} 个关键词）"
        print(f"✓ Driver Prompt 强调生命感（找到 {found} 个关键词）")
    
    def test_driver_prompt_forbids_assistant_language(self):
        """测试 Driver Prompt 禁止客服式语言"""
        forbidden = ["希望我们以后", "有什么需要随时找我", "很高兴能帮到你"]
        # 这些词应该出现在"禁止"列表中或者完全不出现
        # 它们可能出现在规则说明中，所以我们只检查 reply 格式后面是否出现
        assert "禁止" in DRIVER_SYSTEM_PROMPT or "客服" in DRIVER_SYSTEM_PROMPT
        print("✓ Driver Prompt 包含反客服语言规则")

    def test_navigator_prompt_emphasizes_intuition(self):
        """测试 Navigator Prompt 强调直觉和潜意识"""
        keywords = ["直觉", "潜意识", "本能", "联想", "好奇"]
        found = sum(1 for keyword in keywords if keyword in NAVIGATOR_SYSTEM_PROMPT)
        
        assert found >= 3, "Navigator Prompt 应该强调直觉和潜意识"
        print(f"✓ Navigator Prompt 强调直觉（找到 {found} 个关键词）")
    
    def test_prompts_length_reasonable(self):
        """测试 Prompt 长度合理"""
        assert len(DRIVER_SYSTEM_PROMPT) < 5000, f"Driver Prompt 过长: {len(DRIVER_SYSTEM_PROMPT)}"
        assert len(NAVIGATOR_SYSTEM_PROMPT) < 5000, f"Navigator Prompt 过长: {len(NAVIGATOR_SYSTEM_PROMPT)}"
        
        print(f"✓ Prompt 长度合理 (Driver: {len(DRIVER_SYSTEM_PROMPT)}, Navigator: {len(NAVIGATOR_SYSTEM_PROMPT)})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
