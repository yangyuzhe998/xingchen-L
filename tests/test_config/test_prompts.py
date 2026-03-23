"""
测试 xingchen/config/prompts.py
验证 Prompt 模板定义
"""

import pytest
from xingchen.config.prompts import (
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
        print(f"✅ DRIVER_SYSTEM_PROMPT 长度: {len(DRIVER_SYSTEM_PROMPT)} 字符")
    
    def test_navigator_system_prompt_exists(self):
        """测试 Navigator 系统 Prompt 存在且非空"""
        assert NAVIGATOR_SYSTEM_PROMPT
        assert len(NAVIGATOR_SYSTEM_PROMPT) > 100
        assert "潜意识" in NAVIGATOR_SYSTEM_PROMPT or "S脑" in NAVIGATOR_SYSTEM_PROMPT
        print(f"✅ NAVIGATOR_SYSTEM_PROMPT 长度: {len(NAVIGATOR_SYSTEM_PROMPT)} 字符")
    
    def test_proactive_driver_prompt_exists(self):
        """测试主动对话 Prompt 存在"""
        assert PROACTIVE_DRIVER_PROMPT
        assert "沉默" in PROACTIVE_DRIVER_PROMPT or "主动" in PROACTIVE_DRIVER_PROMPT
        print(f"✅ PROACTIVE_DRIVER_PROMPT 长度: {len(PROACTIVE_DRIVER_PROMPT)} 字符")
    
    def test_navigator_user_prompt_exists(self):
        """测试 Navigator 用户 Prompt 存在"""
        assert NAVIGATOR_USER_PROMPT
        assert "交互日志" in NAVIGATOR_USER_PROMPT or "日志" in NAVIGATOR_USER_PROMPT
        print(f"✅ NAVIGATOR_USER_PROMPT 长度: {len(NAVIGATOR_USER_PROMPT)} 字符")
    
    def test_cognitive_graph_prompt_exists(self):
        """测试认知图谱 Prompt 存在"""
        assert COGNITIVE_GRAPH_PROMPT
        assert "图谱" in COGNITIVE_GRAPH_PROMPT or "实体" in COGNITIVE_GRAPH_PROMPT
        print(f"✅ COGNITIVE_GRAPH_PROMPT 长度: {len(COGNITIVE_GRAPH_PROMPT)} 字符")
    
    def test_diary_generation_prompt_exists(self):
        """测试日记生成 Prompt 存在"""
        assert DIARY_GENERATION_PROMPT
        assert "日记" in DIARY_GENERATION_PROMPT
        print(f"✅ DIARY_GENERATION_PROMPT 长度: {len(DIARY_GENERATION_PROMPT)} 字符")
    
    def test_fact_extraction_prompt_exists(self):
        """测试事实提取 Prompt 存在"""
        assert FACT_EXTRACTION_PROMPT
        assert "事实" in FACT_EXTRACTION_PROMPT
        print(f"✅ FACT_EXTRACTION_PROMPT 长度: {len(FACT_EXTRACTION_PROMPT)} 字符")
    
    def test_alias_extraction_prompt_exists(self):
        """测试别名提取 Prompt 存在"""
        assert ALIAS_EXTRACTION_PROMPT
        assert "别名" in ALIAS_EXTRACTION_PROMPT or "昵称" in ALIAS_EXTRACTION_PROMPT
        print(f"✅ ALIAS_EXTRACTION_PROMPT 长度: {len(ALIAS_EXTRACTION_PROMPT)} 字符")
    
    def test_memory_summary_prompt_exists(self):
        """测试记忆总结 Prompt 存在"""
        assert MEMORY_SUMMARY_PROMPT
        assert "记忆" in MEMORY_SUMMARY_PROMPT or "整合" in MEMORY_SUMMARY_PROMPT
        print(f"✅ MEMORY_SUMMARY_PROMPT 长度: {len(MEMORY_SUMMARY_PROMPT)} 字符")

    def test_graph_extraction_prompt_exists(self):
        """测试图谱提取 Prompt 存在"""
        assert GRAPH_EXTRACTION_PROMPT
        assert "图谱" in GRAPH_EXTRACTION_PROMPT or "实体" in GRAPH_EXTRACTION_PROMPT
        print(f"✅ GRAPH_EXTRACTION_PROMPT 长度: {len(GRAPH_EXTRACTION_PROMPT)} 字符")
    
    def test_autonomous_learning_prompt_exists(self):
        """测试自主学习 Prompt 存在"""
        assert AUTONOMOUS_LEARNING_TRIGGER_PROMPT
        assert "学习" in AUTONOMOUS_LEARNING_TRIGGER_PROMPT or "好奇" in AUTONOMOUS_LEARNING_TRIGGER_PROMPT
        print(f"✅ AUTONOMOUS_LEARNING_TRIGGER_PROMPT 长度: {len(AUTONOMOUS_LEARNING_TRIGGER_PROMPT)} 字符")

    def test_knowledge_internalization_prompt_exists(self):
        """测试知识内化 Prompt 存在"""
        assert KNOWLEDGE_INTERNALIZATION_PROMPT
        assert "知识" in KNOWLEDGE_INTERNALIZATION_PROMPT
        print(f"✅ KNOWLEDGE_INTERNALIZATION_PROMPT 长度: {len(KNOWLEDGE_INTERNALIZATION_PROMPT)} 字符")
