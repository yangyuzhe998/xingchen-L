from ....config.settings.settings import settings
from ....utils.logger import logger
from ....utils.json_parser import extract_json
from ....config.prompts.prompts import (
    NAVIGATOR_USER_PROMPT
)
from ...managers.library_manager import library_manager
from ....core.bus.event_bus import event_bus

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
                 skill_info = "【相关技能推荐 (Skill Library)】\n"
                 for s in skills:
                     skill_info += f"- {s['name']}: {s['description']}\n"
        
        static_system_prompt = self.context_manager.build_static_context()
        
        dynamic_user_prompt = NAVIGATOR_USER_PROMPT.format(
            long_term_context=long_term_context,
            skill_info=skill_info,
            script=script
        )

        try:
            # 模拟 R1 的长思考过程
            response = self.llm.chat([
                {"role": "system", "content": static_system_prompt},
                {"role": "user", "content": dynamic_user_prompt}
            ])
            
            if response is None:
                logger.error(f"[Reasoner] S脑分析失败 (LLM Error)")
                return None, None, None

            logger.debug(f"[Reasoner] R1 回复:\n{response}")

            # [Parser Upgrade] 使用 extract_json
            parsed_data = extract_json(response)
            
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
                    
                # 5. Proactive Instruction [New]
                if "proactive_instruction" in parsed_data:
                    proactive_instruction = parsed_data["proactive_instruction"]
                    logger.info(f"[Reasoner] [Proactive] 生成主动指令: {proactive_instruction}")

            # 返回结果 (Suggestion 用于注入 Driver, Delta 用于更新心智, Instruction 用于主动触发)
            return suggestion, delta, proactive_instruction
            
        except Exception as e:
            logger.error(f"[Reasoner] 周期分析异常: {e}", exc_info=True)
            return None, None, None
