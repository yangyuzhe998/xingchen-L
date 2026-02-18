from src.config.settings.settings import settings
from src.utils.logger import logger
from src.utils.json_parser import extract_json
import json
from src.config.prompts.prompts import (
    NAVIGATOR_USER_PROMPT
)
from src.core.managers.library_manager import library_manager
from src.tools.registry import tool_registry
from src.tools.definitions import ToolTier
from src.core.bus.event_bus import event_bus
from src.psyche import value_system

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
            
            # 处理 Payload: 使用统一接口
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
        # S脑使用全量摘要 + 弱相关联想 (Hybrid Mode)
        long_term_context = self.memory.get_relevant_long_term(
            query=script, # 用整个对话脚本作为 Context 检索线索
            limit=10, 
            search_mode="hybrid"
        )

        # [New] 检索相关技能
        last_user_msg = ""
        for e in reversed(events):
            if e.type == "user_input":
                # 安全获取 Payload 内容
                last_user_msg = e.get_content()
                break
        
        skill_info = ""
        if last_user_msg:
             skills = library_manager.search_skills(last_user_msg, top_k=3)
             if skills:
                 skill_info += "【相关技能推荐 (Skill Library)】\n"
                 for s in skills:
                     skill_info += f"- {s['name']}: {s['description']}\n"
        
        # [New] 强制注入 SLOW 级别的工具 (如 web_crawl)
        # 确保 S脑 总是知道它有能力调用这些深度工具
        slow_tools_context = self.context_manager.get_slow_tools_context()
        if slow_tools_context:
            skill_info += slow_tools_context
        
        static_system_prompt = self.context_manager.build_static_context()
        
        # [New] 检测是否由 IdleTrigger 触发的特定意图
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

        # [Phase 5.2] 注入探索意图引导
        if idle_intent == "exploration":
            dynamic_user_prompt += "\n\n(系统提示：当前你产生了强烈的【自主探索】欲。请优先考虑搜索新知识、分析系统现状或产生进化的渴望。)"
        elif idle_intent == "connection":
            dynamic_user_prompt += "\n\n(系统提示：当前你产生了强烈的【社交联结】欲。请考虑主动向用户发起一段有深度或有温度的话题。)"

        try:
            # [Phase 5.2] 增加工具循环支持
            messages = [
                {"role": "system", "content": static_system_prompt},
                {"role": "user", "content": dynamic_user_prompt}
            ]
            
            raw_response = None
            # 获取 SLOW 级别的工具定义
            tools = tool_registry.get_openai_tools(tier=ToolTier.SLOW)
            # 同时也加上 FAST 级别的工具，让 S 脑拥有全量能力
            tools.extend(tool_registry.get_openai_tools(tier=ToolTier.FAST))

            for i in range(3): # 最多循环 3 次
                response = self.llm.chat(messages, tools=tools)
                if not response:
                    break
                
                # 如果是纯文本回复
                if isinstance(response, str):
                    raw_response = response
                    break
                
                # 如果是工具调用
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    # 记录助手的调用请求
                    if hasattr(response, 'model_dump'):
                        messages.append(response.model_dump())
                    else:
                        messages.append(response.to_dict() if hasattr(response, 'to_dict') else response)
                    
                    for tool_call in response.tool_calls:
                        name = tool_call.function.name
                        args_str = tool_call.function.arguments
                        logger.info(f"[Reasoner] 🛠️ S脑执行工具: {name} Args: {args_str}")
                        try:
                            args = json.loads(args_str)
                            result = tool_registry.execute(name, **args)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": name,
                                "content": str(result)
                            })
                        except Exception as e:
                            logger.error(f"[Reasoner] 工具执行失败: {e}")
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": name,
                                "content": f"Error: {e}"
                            })
                    continue # 继续循环让 LLM 总结
                else:
                    raw_response = getattr(response, 'content', None)
                    break

            if raw_response is None:
                # [Fix] 工具循环耗尽但未产生文本回复：追加一轮无工具调用，强制输出
                logger.warning(f"[Reasoner] 工具循环耗尽，强制请求文本总结...")
                messages.append({"role": "user", "content": "请根据以上工具调用的结果，直接输出你的 JSON 分析结论。不要再调用工具。"})
                fallback_response = self.llm.chat(messages, tools=None)
                if fallback_response:
                    if isinstance(fallback_response, str):
                        raw_response = fallback_response
                    else:
                        raw_response = getattr(fallback_response, 'content', None)

            if raw_response is None:
                logger.error(f"[Reasoner] S脑分析失败 (LLM Error)")
                return None, None, None

            logger.debug(f"[Reasoner] R1 回复:\n{raw_response}")

            # [Parser Upgrade] 使用 extract_json
            parsed_data = extract_json(raw_response)
            
            suggestion = "维持当前策略。"
            delta = None
            proactive_instruction = None # [New]
            
            if parsed_data:
                # 1. Suggestion
                suggestion = parsed_data.get("suggestion", suggestion)
                
                # 2. Psyche Delta
                if "psyche_delta" in parsed_data:
                    delta = parsed_data["psyche_delta"]
                    
                # 3. Memories
                if "memories" in parsed_data:
                    for mem in parsed_data["memories"]:
                        content = mem.get("content")
                        cat = mem.get("category", "instinct")
                        if content:
                            self.memory.add_long_term(content, category=cat)
                            logger.info(f"[Reasoner] [S-Brain] 新增深度记忆 ({cat}): {content}")
                            
                # 4. Evolution
                if "evolution_request" in parsed_data:
                    ev_req = parsed_data["evolution_request"]
                    logger.info(f"[Reasoner] [Evolution] S脑渴望进化: {ev_req}")
                    
                # 5. Proactive Instruction
                if "proactive_instruction" in parsed_data:
                    proactive_instruction = parsed_data["proactive_instruction"]
                    logger.info(f"[Reasoner] [Proactive] 生成主动指令: {proactive_instruction}")

                # 6. [Phase 4.2] 价值观自我立法 (Self-Written Codex)
                if "new_values" in parsed_data:
                    for val in parsed_data["new_values"]:
                        value_system.add_value(val, source_emotion="S-Brain Reflection")
                if "revoked_values" in parsed_data:
                    for val in parsed_data["revoked_values"]:
                        value_system.revoke_value(val)

            # 返回结果 (Suggestion 用于注入 Driver, Delta 用于更新心智, Instruction 用于主动触发)
            return suggestion, delta, proactive_instruction
            
        except Exception as e:
            logger.error(f"[Reasoner] 周期分析异常: {e}", exc_info=True)
            return None, None, None
