import json
import threading
import time
from datetime import datetime
from ...utils.llm_client import LLMClient
from ...utils.logger import logger
from ...utils.json_parser import extract_json
from ...memory.memory_core import Memory
from ..bus.event_bus import event_bus, Event
from ..managers.library_manager import library_manager
from ...psyche import psyche_engine, mind_link
from ...config.prompts.prompts import DRIVER_SYSTEM_PROMPT, PROACTIVE_DRIVER_PROMPT
from ...config.settings.settings import settings
from ...tools.registry import tool_registry

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
            instruction = event.payload.get("content")
            if instruction:
                # 在新线程中执行，避免阻塞事件总线分发
                threading.Thread(target=self.proactive_speak, args=(instruction,), daemon=True).start()

    def proactive_speak(self, instruction):
        """
        [New] 主动发起对话 (基于 S脑 指令)
        """
        # 1. 冷却检查
        if time.time() - self.last_interaction_time < settings.PROACTIVE_COOLDOWN:
            logger.info(f"[{self.name}] 处于冷却期，跳过主动发言指令: {instruction[:20]}...")
            return

        # 如果正在思考（处理用户输入），则忽略这次主动尝试
        if not self._thinking_lock.acquire(blocking=False):
            logger.info(f"[{self.name}] 正在忙于回复用户，忽略主动干预指令: {instruction}")
            return

        try:
            print(f"\n[{self.name}] ⚡ 收到潜意识冲动: {instruction}")
            
            # [Fix] 确保 instruction 是字符串，如果是字典则转为 JSON 字符串
            instruction_str = json.dumps(instruction, ensure_ascii=False) if isinstance(instruction, (dict, list)) else str(instruction)
            
            current_psyche = psyche_engine.get_state_summary()
            # 使用转换后的字符串进行检索
            long_term_context = self.memory.get_relevant_long_term(query=instruction_str, limit=5)
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
            
            if response:
                try:
                    parsed = extract_json(response)
                    reply = parsed.get("reply", response) if parsed else response
                    inner_voice = parsed.get("inner_voice", "我想说话...") if parsed else ""
                    emotion = parsed.get("emotion", "curious") if parsed else "neutral"
                except:
                    reply = response
                    inner_voice = ""
                    emotion = "neutral"

                # 输出结果
                # 注意：在 CLI 模式下，这可能会打断用户的输入行，这是已知限制
                print(f"\n[{self.name}] (主动): {reply}")
                
                # 存入短期记忆
                self.memory.add_short_term("assistant", reply)
                
                # 发布事件
                event_bus.publish(Event(
                    type="driver_response",
                    source="driver",
                    payload={"content": reply},
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

    def think(self, user_input, psyche_state=None, suggestion=""):
        """
        处理用户输入，做出即时反应。
        支持 Function Calling (工具调用)。
        """
        # 获取锁，标志正在思考
        # 注意：这会阻塞直到获得锁，确保不会与 proactive_speak 冲突
        with self._thinking_lock:
            response = self._think_internal(user_input, psyche_state, suggestion)
            
            # 更新最后互动时间
            self.last_interaction_time = time.time()
            
            return response

    def _think_internal(self, user_input, psyche_state=None, suggestion=""):
        print(f"[{self.name}] 正在思考: {user_input}")
        
        # 1. 尝试演化心智状态 (Input Stimulus)
        # 简单假设：每次用户输入都微弱增加一点好奇，但如果输入太长可能增加懒惰 (这里暂不实现复杂逻辑，留给 S 脑)
        # [New] 根据输入长度和内容简单调整亲密度 (模拟)
        # 在真实场景中，这应该由 S 脑根据情感分析来驱动
        # 这里做一个简单的 Hack: 每次互动微弱增加亲密度
        psyche_engine.update_state({"intimacy": 0.01})

        # 这里只做读取
        current_psyche = psyche_engine.get_state_summary()
        
        # 2. 读取 Mind-Link (潜意识直觉)
        # [Fix] 增加重试/等待机制？暂时保持直接读取，但增加 Log
        intuition = mind_link.read_intuition()
        if intuition:
             logger.info(f"[{self.name}] 🧠 感知到潜意识直觉: {intuition[:30]}...")
        
        # 获取长期记忆上下文 (传入 user_input 以进行关键词检索)
        long_term_context = self.memory.get_relevant_long_term(query=user_input)
        
        # [New] 模糊别名解析 (Fuzzy Alias Resolution)
        # 尝试从用户输入中检索是否包含已知的别名
        try:
            alias_match = self.memory.search_alias(query=user_input, threshold=0.4)
            if alias_match:
                alias, target, dist = alias_match
                print(f"[{self.name}] 🔍 检测到模糊别名: '{alias}' -> '{target}' (dist: {dist:.4f})")
                # 注入别名解释到 Context
                alias_context = f"\n[System Note]: 用户当前提到的 '{alias}' 在系统中被识别为 '{target}'。\n"
                # 如果是“用户”本身，还可以顺便加载用户的 Profile
                if target == "User" or target == "用户":
                    alias_context += "(已自动关联用户画像)\n"
                
                # 将其拼接到 long_term_context 最前方
                long_term_context = alias_context + long_term_context
        except Exception as e:
            print(f"[{self.name}] 别名检索异常: {e}")
        
        # [New] 尝试检索图谱中的用户画像 (Graph Profile)
        # 简单检索：直接查找 "用户" 相关的属性和社交关系
        try:
            user_profile = self.memory.graph_storage.get_cognitive_subgraph("用户", relation_type="attribute")
            user_profile += self.memory.graph_storage.get_cognitive_subgraph("用户", relation_type="social")
            if user_profile:
                profile_str = "\n【用户画像 (Graph Memory)】:\n"
                for p in user_profile:
                    # 格式化: 用户 --[relation]--> target (meta)
                    profile_str += f"- 用户 {p['relation']} {p['target']}"
                    if p.get('meta') and p['meta'].get('emotion_tag'):
                         profile_str += f" (Emotion: {p['meta']['emotion_tag']})"
                    profile_str += "\n"
                long_term_context += profile_str
        except Exception as e:
            logger.warning(f"[{self.name}] 图谱画像检索失败: {e}")
            
        # 搜索相关技能
        relevant_skills = library_manager.search_skills(user_input, top_k=2)
        skill_info = ""
        if relevant_skills:
            skill_info = "【相关技能推荐】:\n"
            for skill in relevant_skills:
                skill_info += f"- {skill['name']} (ID: {skill['id']}): {skill['description']}\n"
            skill_info += "(如果需要使用，请调用 `read_skill` 获取详细指南，或直接尝试 `run_shell_command` 如果你知道怎么用)"

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        system_prompt = DRIVER_SYSTEM_PROMPT.format(
            current_time=current_time,
            psyche_desc=current_psyche,
            suggestion=intuition,
            long_term_context=long_term_context,
            skill_info=skill_info
        )
        
        messages = [
            {"role": "system", "content": system_prompt} 
        ]
        
        # 从 Memory 模块获取最近历史 (修正为 15 轮)
        messages.extend(self.memory.get_recent_history(limit=15))
        messages.append({"role": "user", "content": user_input})
        
        # 发布 UserInput 事件到总线
        event_bus.publish(Event(
            type="user_input",
            source="user",
            payload={"content": user_input},
            meta={}
        ))

        # 准备工具 (获取所有可用工具)
        tools = tool_registry.get_openai_tools()
        
        raw_response = None
        
        # 工具调用循环 (最多 3 轮)
        for _ in range(3):
            response = self.llm.chat(messages, tools=tools)
            
            if not response:
                break
                
            # 1. 如果是纯文本 (无工具调用)，直接结束
            if isinstance(response, str):
                raw_response = response
                break
                
            # 2. 如果有工具调用
            if response.tool_calls:
                # 将 Assistant 的回复 (包含 tool_calls) 加入历史
                # 必须转为 dict，否则后续 LLMClient 计算长度会报错
                if hasattr(response, 'model_dump'):
                    messages.append(response.model_dump())
                elif hasattr(response, 'to_dict'):
                    messages.append(response.to_dict())
                else:
                    messages.append(response)
                
                # 执行所有工具调用
                for tool_call in response.tool_calls:
                    function_name = tool_call.function.name
                    function_args = tool_call.function.arguments
                    call_id = tool_call.id
                    
                    print(f"[{self.name}] 🛠️ 正在调用工具: {function_name} Args: {function_args}")
                    
                    try:
                        args = json.loads(function_args)
                        result = tool_registry.execute(function_name, **args)
                        # Truncate result for display
                        display_result = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
                        print(f"[{self.name}] 🛠️ 工具执行结果: {display_result}")
                    except Exception as e:
                        result = f"Error: {str(e)}"
                        print(f"[{self.name}] 🛠️ 工具执行出错: {e}")
                    
                    # 将工具结果加入历史
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": function_name,
                        "content": str(result)
                    })
                
                # 继续下一轮循环，让 LLM 根据工具结果生成最终回复
                continue
            else:
                # 虽然是 Message 对象但没有 tool_calls (可能是 content)
                raw_response = response.content
                break
        
        # [New] 手动触发深度维护 (Deep Clean)
        if "深度维护" in user_input or "/deep_clean" in user_input:
            logger.info(f"[{self.name}] 收到深度维护指令，正在转发给 S 脑...")
            if hasattr(self.memory, 'navigator') and self.memory.navigator:
                 # 异步触发，不阻塞当前对话
                 threading.Thread(target=self.memory.navigator.deep_clean_manager.perform_deep_clean, args=("manual",), daemon=True).start()
                 reply = "好的，正在启动深度维护程序。这可能需要几分钟时间，请稍候..."
                 inner_voice = "系统维护"
                 emotion = "serious"
                 # 直接返回，跳过 LLM 解析
                 self.memory.add_short_term("user", user_input)
                 self.memory.add_short_term("assistant", reply)
                 event_bus.publish(Event(type="driver_response", source="driver", payload={"content": reply}, meta={"inner_voice": inner_voice}))
                 return reply

        if raw_response is None:
            # 处理 LLM 故障的降级方案
            print(f"[{self.name}] LLM 调用失败，使用降级回复。")
            reply = "抱歉，我现在的思绪有点乱（连接错误），请稍后再试。"
            inner_voice = "系统错误"
            emotion = "error"
        else:
            # 解析 JSON 输出
            try:
                # 使用增强的 JSON 提取器
                parsed_response = extract_json(raw_response)
                
                if parsed_response:
                    reply = parsed_response.get("reply", raw_response)
                    inner_voice = parsed_response.get("inner_voice", "")
                    emotion = parsed_response.get("emotion", "neutral")
                else:
                    raise ValueError("No valid JSON found")
                    
            except Exception as e:
                # 如果解析失败，可能 LLM 并没有返回 JSON，而是直接返回了文本
                # 这在工具调用后尤其常见，虽然 Prompt 要求 JSON，但 LLM 可能“忘”了
                # 我们做个兼容：直接把 raw_response 当作 reply
                logger.warning(f"[{self.name}] JSON解析失败 (使用原始文本): {e}")
                reply = raw_response
                inner_voice = "直接输出"
                emotion = "neutral"

        # 将新的一轮对话存入 ShortTerm Memory
        self.memory.add_short_term("user", user_input)
        self.memory.add_short_term("assistant", reply)
        
        # 发布 DriverResponse 事件到总线 (包含 Meta 数据)
        event_bus.publish(Event(
            type="driver_response",
            source="driver",
            payload={"content": reply},
            meta={
                "inner_voice": inner_voice,
                "user_emotion_detect": emotion,
                "psyche_state": str(psyche_state) if psyche_state else "unknown",
                "suggestion_ref": suggestion
            }
        ))
        
        return reply

    def act(self, action):
        """
        执行具体行动。
        """
        print(f"[{self.name}] 执行行动: {action}")
