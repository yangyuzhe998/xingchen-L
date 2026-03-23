from xingchen.config.settings import settings
from xingchen.utils.logger import logger
from xingchen.utils.json_parser import extract_json
import json
from xingchen.config.prompts import (
    NAVIGATOR_USER_PROMPT
)
from xingchen.managers.library import library_manager
from xingchen.tools.registry import tool_registry
from xingchen.tools.definitions import ToolTier
from xingchen.core.event_bus import event_bus
from xingchen.psyche import value_system


class Reasoner:
    """
    深度思考者 (Reasoner)
    职责：执行 R1 模式的深度推理
    """
    def __init__(self, llm, memory, context_manager):
        self.llm = llm
        self.memory = memory
        self.context_manager = context_manager

    def analyze_cycle(self):
        """
        基于 EventBus 的周期性分析 (R1 模式)
        """
        logger.info(f"[Reasoner] 启动周期性深度推理 (R1 Mode)...")
        
        events = event_bus.get_latest_cycle(limit=50)
        if not events:
            return None, None, None

        script = ""
        for e in events:
            timestamp_str = f"{e.timestamp:.2f}"
            content = e.get_content()

            if e.type == "user_input":
                script += f"[{timestamp_str}] User: {content}\n"
            elif e.type == "driver_response":
                meta = e.meta
                inner_voice = meta.get('inner_voice', 'N/A')
                emotion = meta.get('user_emotion_detect', 'N/A')
                script += f"[{timestamp_str}] Driver (Inner: {inner_voice}) [Detect: {emotion}]: {content}\n"
            elif e.type == "system_heartbeat":
                 script += f"[{timestamp_str}] System: {content}\n"

        # 动态部分：长期记忆 + 最近日志
        long_term_context = self.memory.get_relevant_long_term(
            query=script,
            limit=10, 
            search_mode="hybrid"
        )

        # 检索相关技能
        last_user_msg = ""
        for e in reversed(events):
            if e.type == "user_input":
                last_user_msg = e.get_content()
                break
        
        skill_info = ""
        if last_user_msg:
             skills = library_manager.search_skills(last_user_msg, top_k=3)
             if skills:
                 skill_info += "【相关技能推荐 (Skill Library)】\n"
                 for s in skills:
                     skill_info += f"- {s['name']}: {s['description']}\n"
        
        # 强制注入 SLOW 级别的工具
        slow_tools_context = self.context_manager.get_slow_tools_context()
        if slow_tools_context:
            skill_info += slow_tools_context
        
        static_system_prompt = self.context_manager.build_static_context()
        
        # 检测是否由 IdleTrigger 触发的特定意图
        idle_intent = None
        for e in reversed(events):
            if e.type == "system_heartbeat" and e.meta.get("idle_action"):
                idle_intent = e.meta["idle_action"]
                break

        dynamic_user_prompt = NAVIGATOR_USER_PROMPT.format(
            long_term_context=long_term_context,
            skill_info=skill_info,
            script=script
        )

        if idle_intent == "exploration":
            dynamic_user_prompt += "\n\n(系统提示：当前你产生了强烈的【自主探索】欲。请优先考虑搜索新知识、分析系统现状或产生进化的渴望。)"
        elif idle_intent == "connection":
            dynamic_user_prompt += "\n\n(系统提示：当前你产生了强烈的【社交联结】欲。请考虑主动向用户发起一段有深度或有温度的话题。)"

        try:
            response_obj = self.llm.chat(
                [
                    {"role": "system", "content": static_system_prompt},
                    {"role": "user", "content": dynamic_user_prompt}
                ],
                temperature=0.6 # R1 推理模式通常建议略高的 temperature 以增加发散性
            )
            
            if not response_obj:
                return None, None, None

            response = response_obj.content
            logger.info(f"[Reasoner] R1 推理结果解析中...")
            
            parsed = extract_json(response)
            if not parsed:
                logger.warning(f"[Reasoner] JSON 解析失败，响应内容: {response[:100]}...")
                return response, None, None

            suggestion = parsed.get("suggestion")
            psyche_delta = parsed.get("psyche_delta")
            proactive_instruction = parsed.get("proactive_instruction")
            
            # 存储深层记忆
            memories = parsed.get("memories", [])
            for mem in memories:
                content = mem.get("content")
                category = mem.get("category", "instinct")
                if content:
                    self.memory.add_long_term(f"[Subconscious] {content}", category=category)
            
            # 处理自发规矩 (价值观演化)
            if parsed.get("evolution_request"):
                 req = parsed["evolution_request"]
                 if req.get("tool_name") and req.get("description"):
                     value_system.add_value(f"我渴望拥有 {req['tool_name']} 的能力，因为 {req['description']}", source_emotion="curiosity")

            return suggestion, psyche_delta, proactive_instruction

        except Exception as e:
            logger.error(f"[Reasoner] 深度推理失败: {e}", exc_info=True)
            return None, None, None
