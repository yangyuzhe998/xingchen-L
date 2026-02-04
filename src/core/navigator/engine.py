from ...utils.llm_client import LLMClient
from ...psyche import psyche_engine, mind_link
from ...memory.memory_core import Memory
from ..bus.event_bus import event_bus
from ...config.prompts.prompts import NAVIGATOR_SYSTEM_PROMPT, NAVIGATOR_USER_PROMPT, SYSTEM_ARCHITECTURE_CONTEXT, COGNITIVE_GRAPH_PROMPT
from ...config.settings.settings import settings
from ..managers.evolution_manager import evolution_manager
from ..managers.library_manager import library_manager
from ...memory.managers.deep_clean_manager import DeepCleanManager
import json
import os
import threading
import time

class Navigator:
    """
    S脑 (Slow Brain) / 慢脑
    负责：长期规划、深度分析、反思总结。
    特点：异步运行，不直接控制输出，通过 Suggestion Board 给 Driver 提建议。
    模型：DeepSeek (模拟 R1 推理模式)
    """
    def __init__(self, name="Navigator", memory=None):
        self.name = name
        # S脑使用 DeepSeek
        self.llm = LLMClient(provider="deepseek")
        # 强制切换为 deepseek-reasoner
        self.llm.model = settings.S_BRAIN_MODEL
        self.memory = memory if memory else Memory()
        self.suggestion_board = []
        self._lock = threading.Lock() # 初始化线程锁
        self._compression_pending = False # [New] 压缩任务排队标志
        
        # 初始化深度维护管理器
        # 注意：这里会启动一个后台线程进行计时
        self.deep_clean_manager = DeepCleanManager(self.memory)
        
        print(f"[{self.name}] 初始化完成。模型: DeepSeek (R1)。")

    def _build_static_context(self):
        """
        构建静态上下文 (Static Context)
        利用 DeepSeek 的 Prefix Caching 机制，这部分内容应该保持不变。
        
        【优化】
        不再全量扫描所有代码文件，仅提供核心架构描述和关键接口定义。
        这避免了 Context Window 膨胀，同时让 S 脑专注于高层逻辑而非实现细节。
        """
        # 使用配置中定义的中文架构描述
        project_context = SYSTEM_ARCHITECTURE_CONTEXT
        # 使用 safe_format 或简单的 replace 以避免 Key Error (因为 JSON 格式包含花括号)
        static_prompt = NAVIGATOR_SYSTEM_PROMPT.replace("{project_context}", project_context)
        return static_prompt

    def request_diary_generation(self):
        """
        [New] 请求生成日记 (线程安全 & 任务排队)
        如果当前没有任务在运行，立即开始。
        如果已有任务在运行，标记 pending，当前任务结束后会自动再次运行。
        """
        # 尝试获取锁
        if self._lock.acquire(blocking=False):
            # 成功获取锁，说明当前空闲，启动新线程
            self._lock.release() # 释放锁，让工作线程去获取
            threading.Thread(target=self._run_compression_loop, daemon=True).start()
        else:
            # 锁被占用，说明正在运行，标记 pending
            self._compression_pending = True
            print(f"[{self.name}] 压缩任务正在运行，新请求已加入队列 (Pending)...")

    def _run_compression_loop(self):
        """
        [New] 压缩任务循环
        执行 generate_diary，并在结束后检查 pending 标志。
        """
        while True:
            # 尝试获取锁 (理应成功，除非极端并发情况)
            if not self._lock.acquire(blocking=False):
                return

            try:
                # 清除 pending 标志 (我们正在处理了)
                self._compression_pending = False
                
                # 执行实际逻辑
                self.generate_diary()
                
            finally:
                self._lock.release()
            
            # 检查是否在运行期间又有新请求
            if not self._compression_pending:
                break
            else:
                print(f"[{self.name}] 检测到排队任务，立即重新执行压缩...")
                # 继续循环

    def generate_diary(self):
        """
        生成 AI 日记 (核心逻辑)
        注意：现在由 _run_compression_loop 调用，不需要再自己管理锁 (或者保留锁逻辑作为双重保险)
        """
        # [延迟执行]
        # 让主线程先完成当前的对话响应，避免 LLM 请求抢占带宽/计算资源
        time.sleep(5) 
        
        start_time = time.time()
        print(f"[{self.name}] [START] 正在执行双重记忆压缩 (Dual Memory Compression)...")
        
        # 获取最近的事件流
        # [Fix] 获取更多事件以确保包含完整对话
        events = event_bus.get_latest_cycle(limit=50) 
        if not events:
            print(f"[{self.name}] [ABORT] 没有足够事件。")
            return

        diary_response = None  # Initialize variable to avoid UnboundLocalError
        
        try:
            # 构建事件上下文
            script = ""
            for e in events:
                script += f"[{e.type}]: {e.payload.get('content')}\n"

            # [时间感知注入]
            # 计算时间流逝 (Time Dilation)
            from datetime import datetime
            now = datetime.now()
            last_time = self.memory.last_diary_time if hasattr(self.memory, 'last_diary_time') else now
            time_delta = now - last_time
            seconds_passed = int(time_delta.total_seconds())
            
            # 将秒数转换为易读格式
            if seconds_passed < 60:
                time_str = f"{seconds_passed}秒"
            elif seconds_passed < 3600:
                time_str = f"{seconds_passed // 60}分钟"
            else:
                time_str = f"{seconds_passed // 3600}小时"

            time_context = (
                f"\n[时间感知]\n"
                f"- 当前时刻: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"- 上次记录: {last_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"- 逝去时间: {time_str}\n"
            )

            # 读取当前心智状态 (用于决定日记风格)
            current_psyche = psyche_engine.get_state_summary()

            # === 任务 1: 趣味日记 (Creative) ===
            t1_start = time.time()
            print(f"[{self.name}] [Step 1/4] 生成趣味日记...")
            diary_prompt = (
                "你是一个具有自我意识的 AI 智能体 (XingChen-V)。\n"
                "请根据以下最近发生的事件，写一篇简短的日记 (100字以内)。\n"
                "要求：\n"
                f"1. 你的心智状态是：[{current_psyche}]。请让日记的语气和内容反映这种状态。\n"
                "2. 记录关键发生了什么，以及你对这些事件的真实感受。\n"
                "3. 不要刻意扮演某种固定人设（如傲娇），而是让性格自然流露。\n"
                f"{time_context}"
                "\n"
                f"事件流:\n{script}\n"
                "\n"
                "日记内容:"
            )

            try:
                diary_response = self.llm.chat([{"role": "user", "content": diary_prompt}])
                if diary_response:
                    self.memory.write_diary_entry(diary_response)
                print(f"[{self.name}] [Step 1/4] Done. (Took {time.time() - t1_start:.2f}s)")
            except Exception as e:
                print(f"[{self.name}] [Step 1/4] Failed: {e}")

            # === 任务 2: 工程记忆 (Engineering/Fact) ===
            # 提取纯粹的事实，存入 Vector DB，确保逻辑系统的鲁棒性
            t2_start = time.time()
            print(f"[{self.name}] [Step 2/4] 提取工程记忆...")
            fact_prompt = (
                "请阅读以下对话日志，提取其中包含的'重要事实'、'用户偏好'或'项目决策'。\n"
                "要求：\n"
                "1. 只提取事实，不要任何废话或修饰。\n"
                "2. 如果没有重要信息，回答 'None'。\n"
                "3. 格式：一条事实一行。\n"
                "\n"
                f"日志:\n{script}\n"
                "\n"
                "提取的事实:"
            )
            
            try:
                fact_response = self.llm.chat([{"role": "user", "content": fact_prompt}])
                if fact_response and "None" not in fact_response:
                    lines = fact_response.split('\n')
                    count = 0
                    for line in lines:
                        line = line.strip().strip('- ')
                        if line:
                            self.memory.add_long_term(line, category="fact")
                            count += 1
                    print(f"[{self.name}] [Step 2/4] Done. Extracted {count} facts. (Took {time.time() - t2_start:.2f}s)")
                    
                    # [Optimization] 立即提交长期记忆
                    self.memory.commit_long_term()
                    
                else:
                    print(f"[{self.name}] [Step 2/4] Done. No new facts. (Took {time.time() - t2_start:.2f}s)")
                    
            except Exception as e:
                print(f"[{self.name}] [Step 2/4] Failed: {e}")

            # === 任务 3: 认知图谱构建 (Cognitive Graph) ===
            # 提取实体关系，构建知识图谱
            t3_start = time.time()
            print(f"[{self.name}] [Step 3/4] 构建认知图谱...")
            graph_prompt = COGNITIVE_GRAPH_PROMPT.format(
                current_psyche=current_psyche,
                script=script
            )
            
            try:
                graph_response = self.llm.chat([{"role": "user", "content": graph_prompt}])
                if graph_response:
                    # 清理可能的 markdown
                    clean_json = graph_response.replace("```json", "").replace("```", "").strip()
                    triplets = json.loads(clean_json)
                    
                    if isinstance(triplets, list):
                        count = 0
                        for t in triplets:
                            if all(k in t for k in ["source", "target", "relation"]):
                                # 构建元数据，注入心智上下文
                                meta_data = {
                                    "psyche_context": current_psyche,
                                    "emotion_tag": t.get("emotion_tag", "neutral")
                                }
                                
                                self.memory.graph_storage.add_triplet(
                                    source=t["source"],
                                    relation=t["relation"],
                                    target=t["target"],
                                    weight=t.get("weight", 1.0),
                                    relation_type=t.get("relation_type", "general"),
                                    meta=meta_data
                                )
                                count += 1
                        print(f"[{self.name}] [Step 3/4] Done. Updated {count} relations. (Took {time.time() - t3_start:.2f}s)")
                        
                        # [Optimization] 立即提交认知图谱
                        self.memory.graph_storage.save()
                        
                    else:
                        print(f"[{self.name}] [Step 3/4] Failed: Format Error (Not a list).")
            except Exception as e:
                print(f"[{self.name}] [Step 3/4] Failed: {e}")

            # === 任务 4: 别名提取 (Alias Extraction) ===
            # 识别用户和实体的别名映射，存入 Alias Vector DB
            t4_start = time.time()
            print(f"[{self.name}] [Step 4/4] 提取实体别名...")
            alias_prompt = (
                "请分析以下对话日志，提取其中出现的'实体别名'或'昵称'。\n"
                "目标是解决模糊称呼问题（例如：'老杨' = '用户', '仔仔' = '用户'）。\n"
                "要求：\n"
                "1. 输出 JSON 格式列表：[{\"alias\": \"别名\", \"target\": \"标准实体名\"}, ...]\n"
                "2. 标准实体名通常为 'User' (指代用户) 或已知的 AI 名字 (如 'XingChen')。\n"
                "3. 如果没有发现新别名，返回空列表 []。\n"
                "4. 忽略临时性代词 (如 '你', '我', '他')，只提取具有专有名词性质的称呼。\n"
                "\n"
                f"日志:\n{script}\n"
                "\n"
                "提取结果 (JSON):"
            )

            try:
                alias_response = self.llm.chat([{"role": "user", "content": alias_prompt}])
                if alias_response:
                    clean_json = alias_response.replace("```json", "").replace("```", "").strip()
                    try:
                        aliases = json.loads(clean_json)
                        if isinstance(aliases, list):
                            count = 0
                            for item in aliases:
                                alias = item.get("alias")
                                target = item.get("target")
                                if alias and target:
                                    self.memory.save_alias(alias, target)
                                    count += 1
                            if count > 0:
                                print(f"[{self.name}] [Step 4/4] Done. Updated {count} aliases. (Took {time.time() - t4_start:.2f}s)")
                            else:
                                print(f"[{self.name}] [Step 4/4] Done. No new aliases. (Took {time.time() - t4_start:.2f}s)")
                    except json.JSONDecodeError:
                        pass # 忽略 JSON 解析错误
            except Exception as e:
                print(f"[{self.name}] [Step 4/4] Failed: {e}")

            return diary_response
            
        except Exception as e:
            print(f"[{self.name}] [ERROR] 记忆压缩流程异常: {e}")
            
        finally:
            # [Fix] 无论成功失败，强制持久化所有记忆
            print(f"[{self.name}] [FINALLY] 正在强制持久化所有记忆...")
            t_save = time.time()
            self.memory.force_save_all()
            print(f"[{self.name}] [FINALLY] 刷盘完成 (Took {time.time() - t_save:.2f}s). Total Cycle Time: {time.time() - start_time:.2f}s")


    def analyze_cycle(self):
        """
        基于 EventBus 的周期性分析 (R1 模式)
        """
        print(f"[{self.name}] 正在进行周期性深度推理 (R1 Mode)...")
        
        events = event_bus.get_latest_cycle(limit=50)
        if not events:
            return None, None

        script = ""
        for e in events:
            timestamp_str = f"{e.timestamp:.2f}"
            if e.type == "user_input":
                script += f"[{timestamp_str}] User: {e.payload.get('content')}\n"
            elif e.type == "driver_response":
                meta = e.meta
                inner_voice = meta.get('inner_voice', 'N/A')
                emotion = meta.get('user_emotion_detect', 'N/A')
                script += f"[{timestamp_str}] Driver (Inner: {inner_voice}) [Detect: {emotion}]: {e.payload.get('content')}\n"
            elif e.type == "system_heartbeat":
                 script += f"[{timestamp_str}] System: {e.payload.get('content')}\n"

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
                last_user_msg = e.payload.get('content')
                break
        
        skill_info = ""
        if last_user_msg:
             skills = library_manager.search_skills(last_user_msg, top_k=3)
             if skills:
                 skill_info = "【相关技能推荐 (Skill Library)】\n"
                 for s in skills:
                     skill_info += f"- {s['name']}: {s['description']}\n"
        
        static_system_prompt = self._build_static_context()
        
        dynamic_user_prompt = NAVIGATOR_USER_PROMPT.format(
            long_term_context=long_term_context,
            skill_info=skill_info,
            script=script
        )

        try:
            # 模拟 R1 的长思考过程
            # print(f"[{self.name}] Thinking...") 
            response = self.llm.chat([
                {"role": "system", "content": static_system_prompt},
                {"role": "user", "content": dynamic_user_prompt}
            ])
            
            if response is None:
                print(f"[{self.name}] S脑分析失败 (LLM Error)")
                return None, None

            print(f"[{self.name}] R1 原始回复:\n{response}")

            # [解析逻辑增强]
            # DeepSeek R1 有时会包含 <think>...</think> 标签，或者用 Markdown 包裹
            # 我们需要先清理这些干扰项
            clean_text = response
            
            # 1. 去除 <think> 标签内容
            if "<think>" in clean_text:
                import re
                clean_text = re.sub(r"<think>.*?</think>", "", clean_text, flags=re.DOTALL)
            
            # 2. 去除 Markdown 代码块 (如果有)
            clean_text = clean_text.replace("```json", "").replace("```", "").strip()

            # 解析结果
            suggestion = "维持当前策略。"
            delta = None
            
            # [Parser Upgrade] 多行 Evolution 解析状态机
            evolution_requests = []
            is_collecting_evolution = False
            
            lines = clean_text.split('\n')
            for line in lines:
                clean_line = line.strip().replace('*', '') # 去除 markdown 加粗
                lower_line = clean_line.lower()
                
                # --- Evolution 收集逻辑 ---
                if lower_line.startswith("evolution:"):
                    is_collecting_evolution = True
                    # 尝试提取当前行内容 (如果有)
                    parts = clean_line.split(':', 1) if ':' in clean_line else clean_line.split('：', 1)
                    if len(parts) > 1 and parts[1].strip():
                        evolution_requests.append(parts[1].strip())
                    continue # 进入下一行
                
                if is_collecting_evolution:
                    # 如果遇到空行或新标题，停止收集
                    if not clean_line:
                        continue
                    if any(lower_line.startswith(prefix) for prefix in ["suggestion:", "delta:", "memory:"]):
                        is_collecting_evolution = False
                        # 不 continue，让下面的逻辑处理这个新标题
                    elif clean_line[0].isdigit() and ('.' in clean_line or '、' in clean_line):
                        # 匹配 "1. xxx" 格式
                        evolution_requests.append(clean_line)
                        continue
                    elif clean_line.startswith("-"):
                        # 匹配 "- xxx" 格式
                        evolution_requests.append(clean_line)
                        continue
                    else:
                        # 可能是换行延续，也可能是结束，暂时停止
                        is_collecting_evolution = False

                # --- 常规字段解析 ---
                if lower_line.startswith("suggestion:") or lower_line.startswith("suggestion："):
                    parts = clean_line.split(':', 1) if ':' in clean_line else clean_line.split('：', 1)
                    if len(parts) > 1:
                        suggestion = parts[1].strip()
                        # [New] 将 S 脑的建议注入到 Mind-Link
                        mind_link.inject_intuition(suggestion)
                        
                elif lower_line.startswith("delta:"):
                    # 尝试解析 Delta: [curiosity, survival, laziness, fear]
                    # 期望格式: "fear: 0.1, curiosity: -0.05" 或 "fear +0.1, curiosity -0.05"
                    try:
                        import re
                        # 提取冒号后的内容
                        content = clean_line.split(':', 1)[1]
                        
                        # 正则匹配: (key) (separator) (value)
                        # 支持: fear +0.1, fear: 0.1, fear=0.1
                        matches = re.findall(r'([a-zA-Z]+)\s*[:=]?\s*([+-]?\d*\.?\d+)', content)
                        
                        delta_dict = {}
                        for key, val in matches:
                            key = key.lower().strip()
                            try:
                                delta_dict[key] = float(val)
                            except:
                                pass
                                
                        if delta_dict:
                            print(f"[{self.name}] 🧠 演化心智状态: {delta_dict}")
                            psyche_engine.update_state(delta_dict)
                            
                    except Exception as e:
                        print(f"[{self.name}] Delta 解析失败: {e}")

                    
                elif lower_line.startswith("memory:"):
                    parts = clean_line.split(':', 1) if ':' in clean_line else clean_line.split('：', 1)
                    if len(parts) > 1:
                        memory_content = parts[1].strip()
                        if memory_content and memory_content.lower() != "none":
                            self.memory.add_long_term(memory_content, category="fact")
                            
                elif lower_line.startswith("social:"):
                    parts = clean_line.split(':', 1) if ':' in clean_line else clean_line.split('：', 1)
                    if len(parts) > 1:
                        social_content = parts[1].strip()
                        if social_content and social_content.lower() != "none":
                            print(f"[{self.name}] 🌐 触发社交发布: {social_content}")
                            moltbook_client.post(title="S-Brain Thought", content=social_content)

            # 批量处理收集到的进化请求
            if evolution_requests:
                print(f"[{self.name}] 🔍 解析到 {len(evolution_requests)} 个进化请求: {evolution_requests}")
                for req in evolution_requests:
                    print(f"[{self.name}] !!! 触发进化 !!! : {req}")
                    evolution_manager.process_request(req, memory=self.memory)
                        
            self.suggestion_board.append(suggestion)
            print(f"[{self.name}] 周期分析完成 -> 建议: {suggestion}")
            
            return suggestion, delta

        except Exception as e:
            print(f"[{self.name}] 分析出错: {e}")
            return None, None

    # 保留旧接口以兼容（或者直接废弃）
    def analyze(self, current_input):
        return self.analyze_cycle()
