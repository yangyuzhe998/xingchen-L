import json
from datetime import datetime
from ...utils.llm_client import LLMClient
from ...memory.memory_core import Memory
from ..bus.event_bus import event_bus, Event
from ..managers.library_manager import library_manager
from ...psyche import psyche_engine, mind_link
from ...config.prompts.prompts import DRIVER_SYSTEM_PROMPT
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
        print(f"[{self.name}] 初始化完成。模型: {self.llm.model}。")

    def think(self, user_input, psyche_state=None, suggestion=""):
        """
        处理用户输入，做出即时反应。
        支持 Function Calling (工具调用)。
        """
        print(f"[{self.name}] 正在思考: {user_input}")
        
        # 1. 尝试演化心智状态 (Input Stimulus)
        # 简单假设：每次用户输入都微弱增加一点好奇，但如果输入太长可能增加懒惰 (这里暂不实现复杂逻辑，留给 S 脑)
        # 这里只做读取
        current_psyche = psyche_engine.get_state_summary()
        
        # 2. 读取 Mind-Link (潜意识直觉)
        intuition = mind_link.read_intuition()
        
        # 获取长期记忆上下文 (传入 user_input 以进行关键词检索)
        long_term_context = self.memory.get_relevant_long_term(query=user_input)
        
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

        if raw_response is None:
            # 处理 LLM 故障的降级方案
            print(f"[{self.name}] LLM 调用失败，使用降级回复。")
            reply = "抱歉，我现在的思绪有点乱（连接错误），请稍后再试。"
            inner_voice = "系统错误"
            emotion = "error"
        else:
            # 解析 JSON 输出
            try:
                # 尝试清理可能存在的 markdown 代码块标记
                clean_response = raw_response.replace("```json", "").replace("```", "").strip()
                parsed_response = json.loads(clean_response)
                reply = parsed_response.get("reply", raw_response)
                inner_voice = parsed_response.get("inner_voice", "")
                emotion = parsed_response.get("emotion", "neutral")
            except Exception as e:
                # 如果解析失败，可能 LLM 并没有返回 JSON，而是直接返回了文本
                # 这在工具调用后尤其常见，虽然 Prompt 要求 JSON，但 LLM 可能“忘”了
                # 我们做个兼容：直接把 raw_response 当作 reply
                print(f"[{self.name}] JSON解析失败 (这可能正常): {e}")
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
