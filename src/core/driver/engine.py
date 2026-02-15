import json
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.utils.llm_client import LLMClient
from src.utils.logger import logger
from src.utils.json_parser import extract_json
from src.memory.memory_core import Memory
from src.core.bus.event_bus import event_bus
from src.schemas.events import BaseEvent as Event, DriverResponsePayload, UserInputPayload
from src.core.managers.library_manager import library_manager
from src.psyche import psyche_engine, mind_link
from src.config.prompts.prompts import DRIVER_SYSTEM_PROMPT, PROACTIVE_DRIVER_PROMPT
from src.config.settings.settings import settings
from src.tools.registry import tool_registry

class Driver:
    """
    F脑 (Fast Brain) / 快脑
    负责：实时交互、短期决策、具体行动。
    特点：反应快，直接控制输出，受 Psyche (心智) 影响。
    模型：Qwen (通义千问)
    """
    def __init__(self, name="Driver", memory=None):
        self.name = name
        # F脑使用 Qwen
        self.llm = LLMClient(provider="qwen")
        self.llm.model = settings.F_BRAIN_MODEL
        self.memory = memory if memory else Memory()
        
        # 订阅事件总线
        event_bus.subscribe(self._on_event)
        self._thinking_lock = threading.Lock() # 防止思考冲突
        self.last_interaction_time = 0 # 上次互动时间 (Unix Timestamp)
        
        logger.info(f"[{self.name}] 初始化完成。模型: {self.llm.model}。")

    def _on_event(self, event):
        """事件监听"""
        if event.type == "proactive_instruction":
            # 使用统一接口获取 content
            instruction = event.get_content()
            if instruction:
                # 在新线程中执行，避免阻塞事件总线分发
                threading.Thread(target=self.proactive_speak, args=(instruction,), daemon=True).start()

    def _get_dynamic_cooldown(self) -> float:
        """根据时间与心智状态动态计算主动发言冷却时间"""
        base = float(settings.PROACTIVE_COOLDOWN)
        hour = datetime.now().hour

        # 深夜降低打扰 (23:00-07:00)
        if hour >= 23 or hour < 7:
            base *= 2

        # laziness 高时更不主动
        try:
            laziness = psyche_engine.get_raw_state()["dimensions"]["laziness"]["value"]
            base *= (1 + float(laziness))
        except Exception:
            pass

        return base

    def proactive_speak(self, instruction):
        """
        [New] 主动发起对话 (基于 S脑 指令)
        """
        # 1. 动态冷却检查
        dynamic_cooldown = self._get_dynamic_cooldown()
        if time.time() - self.last_interaction_time < dynamic_cooldown:
            # 安全打印 instruction
            instr_str = str(instruction)
            logger.info(f"[{self.name}] 处于冷却期({dynamic_cooldown:.1f}s)，跳过主动发言指令: {instr_str[:50]}...")
            return

        # 如果正在思考（处理用户输入），则忽略这次主动尝试
        if not self._thinking_lock.acquire(blocking=False):
            logger.info(f"[{self.name}] 正在忙于回复用户，忽略主动干预指令: {instruction}")
            return
            
        try:
            logger.info(f"[{self.name}] ⚡ 收到潜意识冲动: {instruction}")
            
            # [Fix] 确保 instruction 是字符串，如果是字典则转为 JSON 字符串
            instruction_str = json.dumps(instruction, ensure_ascii=False) if isinstance(instruction, (dict, list)) else str(instruction)
            
            current_psyche = psyche_engine.get_state_summary()
            # 使用转换后的字符串进行检索
            long_term_context = self.memory.get_relevant_long_term(query=instruction_str, limit=settings.DEFAULT_LONG_TERM_LIMIT)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            system_prompt = PROACTIVE_DRIVER_PROMPT.format(
                current_time=current_time,
                psyche_desc=current_psyche,
                instruction=instruction_str, # 使用字符串格式
                long_term_context=long_term_context
            )

            # 调用 LLM 生成主动话语
            # 注意：这里不需要 tools，因为只是单纯的开启话题
            response = self.llm.chat([{"role": "system", "content": system_prompt}])
            
            if not response:
                return

            # 解析回复
            reply, inner_voice, emotion = self._parse_proactive_response(response)

            if reply:
                # 输出结果
                # 注意：在 CLI 模式下，这可能会打断用户的输入行，这是已知限制
                logger.info(f"[{self.name}] (主动): {reply}")
                
                # 存入短期记忆
                self.memory.add_short_term("assistant", reply)
                
                # 发布事件
                event_bus.publish(Event(
                    type="driver_response",
                    source="driver",
                    payload=DriverResponsePayload(content=reply),
                    meta={
                        "inner_voice": inner_voice,
                        "user_emotion_detect": emotion,
                        "proactive": True
                    }
                ))
        except Exception as e:
            logger.error(f"[{self.name}] 主动发言失败: {e}", exc_info=True)
        finally:
            self._thinking_lock.release()

    def _parse_proactive_response(self, response: str):
        """解析主动发言的 LLM 响应"""
        try:
            parsed = extract_json(response)
            if parsed:
                return (
                    parsed.get("reply", response),
                    parsed.get("inner_voice", "我想说话..."),
                    parsed.get("emotion", "curious")
                )
        except json.JSONDecodeError as e:
            logger.warning(f"[{self.name}] JSON Parsing Failed: {e}. Raw: {response}")
        
        # 降级处理
        return response, "", "neutral"

    def think(self, user_input: str, psyche_state: Optional[Dict[str, Any]] = None) -> str:
        """
        主思考入口
        :param user_input: 用户输入
        :param psyche_state: (可选) 外部传入的心智状态快照
        :return: 回复内容
        """
        if not user_input:
            return ""

        # 获取锁，标志正在思考
        # 注意：这会阻塞直到获得锁，确保不会与 proactive_speak 冲突
        with self._thinking_lock:
            response = self._think_internal(user_input, psyche_state)
            
            # 更新最后互动时间
            self.last_interaction_time = time.time()
            
            return response

    def _think_internal(self, user_input, psyche_state=None, suggestion=""):
        """重构后的内部思考流程"""
        # 1. 深度维护检查 (保持原有的手动触发逻辑)
        if "深度维护" in user_input or "/deep_clean" in user_input:
            return self._handle_deep_clean(user_input)

        # 2. 准备上下文
        context = self._prepare_context(user_input)
        
        # 3. 组装消息
        messages = self._build_messages(user_input, context)
        
        # 4. 发布 UserInput 事件
        event_bus.publish(Event(
            type="user_input",
            source="user",
            payload=UserInputPayload(content=user_input),
            meta={}
        ))

        # 5. 调用 LLM (含工具循环)
        tools = tool_registry.get_openai_tools()
        raw_response = self._call_llm_with_tools(messages, tools)

        # 6. 解析响应
        reply, inner_voice, emotion = self._parse_driver_response(raw_response)

        # 7. 收尾：存储记忆并发布响应事件
        self._finalize_interaction(user_input, reply, inner_voice, emotion, psyche_state, suggestion)
        
        return reply

    def _prepare_context(self, user_input: str) -> Dict[str, Any]:
        """准备思考所需的全部上下文信息"""
        # A. 更新/读取心智
        # 亲密度变化不在 F 脑硬编码，交由 S 脑/psyche_delta 驱动
        current_psyche = psyche_engine.get_state_summary()
        
        # B. 读取潜意识直觉
        intuition = mind_link.read_intuition()
        if intuition:
            logger.info(f"[{self.name}] 🧠 感知到潜意识直觉: {intuition[:30]}...")
            
        # C. 记忆检索 (含别名解析与画像)
        long_term_context = self.memory.get_relevant_long_term(query=user_input)
        
        # 别名解析
        try:
            alias_match = self.memory.search_alias(query=user_input, threshold=0.4)
            if alias_match:
                alias, target, dist = alias_match
                logger.info(f"[{self.name}] 🔍 检测到模糊别名: '{alias}' -> '{target}' (dist: {dist:.4f})")
                alias_context = f"\n[System Note]: 用户当前提到的 '{alias}' 在系统中被识别为 '{target}'。\n"
                if target in ["User", "用户"]:
                    alias_context += "(已自动关联用户画像)\n"
                long_term_context = alias_context + long_term_context
        except Exception as e:
            logger.warning(f"[{self.name}] 别名检索异常: {e}")

        # 画像检索
        try:
            user_profile = self._get_user_profile_string()
            if user_profile:
                long_term_context = user_profile + "\n" + long_term_context
        except Exception as e:
            logger.warning(f"[{self.name}] 图谱画像检索失败: {e}")

        # D. 技能与工具列表
        relevant_skills = library_manager.search_skills(user_input, top_k=2)
        skill_info = ""
        if relevant_skills:
            skill_info = "【相关技能推荐】:\n" + "".join([f"- {s['name']} (ID: {s['id']}): {s['description']}\n" for s in relevant_skills])
            skill_info += "(如果需要使用，请调用 `read_skill` 获取详细指南，或直接尝试 `run_shell_command` 如果你知道怎么用)"

        all_tools = tool_registry.get_tools()
        tool_list_str = "".join([f"- {t.name}: {t.description}\n" for t in all_tools])

        return {
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "psyche_desc": current_psyche,
            "suggestion": intuition,
            "long_term_context": long_term_context,
            "skill_info": skill_info,
            "tool_list": tool_list_str
        }

    def _get_user_profile_string(self) -> str:
        """从图谱中提取用户画像字符串"""
        user_profile = []
        for name in ["User", "用户"]:
            user_profile.extend(self.memory.graph_storage.get_cognitive_subgraph(name, relation_type="attribute"))
            user_profile.extend(self.memory.graph_storage.get_cognitive_subgraph(name, relation_type="social"))
        
        if not user_profile:
            return ""

        profile_str = "\n【当前用户画像 (Active Profile)】:\n"
        seen_relations = set()
        for p in user_profile:
            rel_key = f"{p['source']}-{p['relation']}-{p['target']}"
            if rel_key in seen_relations: continue
            seen_relations.add(rel_key)
            
            if p['relation'] in ["has_name", "called", "name_is", "名字是"]:
                profile_str += f"- 名字: {p['target']}\n"
            else:
                profile_str += f"- {p['relation']}: {p['target']}"
                if p.get('meta', {}).get('emotion_tag'):
                    profile_str += f" (Emotion: {p['meta']['emotion_tag']})"
                profile_str += "\n"
        return profile_str

    def _build_messages(self, user_input: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """组装 LLM 请求消息列表"""
        system_prompt = DRIVER_SYSTEM_PROMPT.format(**context)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.memory.get_recent_history(limit=15))
        messages.append({"role": "user", "content": user_input})
        return messages

    def _call_llm_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Optional[str]:
        """执行 LLM 调用循环，处理工具调用"""
        raw_response = None
        for _ in range(3): # 最多 3 轮循环
            response = self.llm.chat(messages, tools=tools)
            if not response: break
            
            if isinstance(response, str):
                raw_response = response
                break
                
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # 记录 Assistant 的工具调用回复
                if hasattr(response, 'model_dump'):
                    messages.append(response.model_dump())
                else:
                    messages.append(response.to_dict() if hasattr(response, 'to_dict') else response)
                
                for tool_call in response.tool_calls:
                    res = self._execute_tool(tool_call)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": str(res)
                    })
                continue # 继续下一轮让 LLM 总结结果
            else:
                raw_response = getattr(response, 'content', None)
                break
        return raw_response

    def _execute_tool(self, tool_call) -> str:
        """执行单个工具调用"""
        name = tool_call.function.name
        args_str = tool_call.function.arguments
        logger.info(f"[{self.name}] 🛠️ 正在调用工具: {name} Args: {args_str}")
        try:
            args = json.loads(args_str)
            result = tool_registry.execute(name, **args)
            display_result = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
            logger.info(f"[{self.name}] 🛠️ 工具执行结果: {display_result}")
            return result
        except Exception as e:
            logger.error(f"[{self.name}] 🛠️ 工具执行出错: {e}")
            return f"Error: {str(e)}"

    def _parse_driver_response(self, raw_response: Optional[str]):
        """解析 LLM 原始响应为 (reply, inner_voice, emotion)"""
        if raw_response is None:
            return "抱歉，我现在的思绪有点乱（连接错误），请稍后再试。", "系统错误", "error"

        try:
            parsed = extract_json(raw_response)
            if parsed:
                return (
                    parsed.get("reply", raw_response),
                    parsed.get("inner_voice", ""),
                    parsed.get("emotion", "neutral")
                )
        except Exception as e:
            logger.warning(f"[{self.name}] JSON解析失败 (使用原始文本): {e}")
            
        return raw_response, "直接输出", "neutral"

    def _finalize_interaction(self, user_input, reply, inner_voice, emotion, psyche_state, suggestion):
        """保存记忆并发布最终事件"""
        self.memory.add_short_term("user", user_input)
        self.memory.add_short_term("assistant", reply)
        
        event_bus.publish(Event(
            type="driver_response",
            source="driver",
            payload=DriverResponsePayload(content=reply),
            meta={
                "inner_voice": inner_voice,
                "user_emotion_detect": emotion,
                "psyche_state": str(psyche_state) if psyche_state else "unknown",
                "suggestion_ref": suggestion
            }
        ))

    def _handle_deep_clean(self, user_input: str) -> str:
        """处理深度维护指令"""
        logger.info(f"[{self.name}] 收到深度维护指令，正在转发给 S 脑...")
        reply = "好的，正在启动深度维护程序。这可能需要几分钟时间，请稍候..."
        if hasattr(self.memory, 'navigator') and self.memory.navigator:
            threading.Thread(target=self.memory.navigator.deep_clean_manager.perform_deep_clean, args=("manual",), daemon=True).start()
        
        self.memory.add_short_term("user", user_input)
        self.memory.add_short_term("assistant", reply)
        event_bus.publish(Event(
            type="driver_response",
            source="driver",
            payload=DriverResponsePayload(content=reply),
            meta={"inner_voice": "系统维护"}
        ))
        return reply

    def act(self, action):
        """执行具体行动。[Deprecated: 行动已通过工具系统执行]"""
        logger.warning(f"[{self.name}] act() 已废弃，请使用工具系统。Action: {action}")