from ...utils.llm_client import LLMClient
from ...psyche import psyche_engine, mind_link
from ...memory.memory_core import Memory
from ..bus.event_bus import event_bus
from ...config.prompts.prompts import (
    NAVIGATOR_SYSTEM_PROMPT, 
    NAVIGATOR_USER_PROMPT, 
    SYSTEM_ARCHITECTURE_CONTEXT, 
    COGNITIVE_GRAPH_PROMPT,
    DIARY_GENERATION_PROMPT,
    FACT_EXTRACTION_PROMPT,
    ALIAS_EXTRACTION_PROMPT
)
from ...config.settings.settings import settings
from ..managers.evolution_manager import evolution_manager
from ..managers.library_manager import library_manager
from ...memory.managers.deep_clean_manager import DeepCleanManager
import json
import os
import threading
import time
from ...utils.logger import logger
from ...utils.json_parser import extract_json

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
            logger.info(f"[{self.name}] 压缩任务正在运行，新请求已加入队列 (Pending)...")

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
                logger.info(f"[{self.name}] 检测到排队任务，立即重新执行压缩...")
                # 继续循环

    def generate_diary(self):
        """
        生成 AI 日记 (核心逻辑)
        注意：现在由 _run_compression_loop 调用，不需要再自己管理锁 (或者保留锁逻辑作为双重保险)
        """
        # [延迟执行]
        # 让主线程先完成当前的对话响应，避免 LLM 请求抢占带宽/计算资源
        time.sleep(settings.NAVIGATOR_DELAY_SECONDS) 
        
        start_time = time.time()
        logger.info(f"[{self.name}] [START] 正在执行双重记忆压缩 (Dual Memory Compression)...")
        
        # 获取最近的事件流
        # [Fix] 获取更多事件以确保包含完整对话
        events = event_bus.get_latest_cycle(limit=settings.NAVIGATOR_EVENT_LIMIT) 
        if not events:
            logger.info(f"[{self.name}] [ABORT] 没有足够事件。")
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
            logger.info(f"[{self.name}] [Step 1/4] 生成趣味日记...")
            diary_prompt = DIARY_GENERATION_PROMPT.format(
                current_psyche=current_psyche,
                time_context=time_context,
                script=script
            )

            try:
                diary_response = self.llm.chat([{"role": "user", "content": diary_prompt}])
                if diary_response:
                    self.memory.write_diary_entry(diary_response)
                logger.info(f"[{self.name}] [Step 1/4] Done. (Took {time.time() - t1_start:.2f}s)")
            except Exception as e:
                logger.error(f"[{self.name}] [Step 1/4] Failed: {e}", exc_info=True)

            # === 任务 2: 工程记忆 (Engineering/Fact) ===
            # 提取纯粹的事实，存入 Vector DB，确保逻辑系统的鲁棒性
            t2_start = time.time()
            print(f"[{self.name}] [Step 2/4] 提取工程记忆...")
            fact_prompt = FACT_EXTRACTION_PROMPT.format(script=script)
            
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
                    logger.info(f"[{self.name}] [Step 2/4] Done. No new facts. (Took {time.time() - t2_start:.2f}s)")
                    
            except Exception as e:
                logger.error(f"[{self.name}] [Step 2/4] Failed: {e}", exc_info=True)

            # === 任务 3: 认知图谱构建 (Cognitive Graph) ===
            # 提取实体关系，构建知识图谱
            t3_start = time.time()
            logger.info(f"[{self.name}] [Step 3/4] 构建认知图谱...")
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
                        logger.info(f"[{self.name}] [Step 3/4] Done. Updated {count} relations. (Took {time.time() - t3_start:.2f}s)")
                        
                        # [Optimization] 立即提交认知图谱
                        self.memory.graph_storage.save()
                        
                    else:
                        logger.warning(f"[{self.name}] [Step 3/4] Failed: Format Error (Not a list).")
            except Exception as e:
                logger.error(f"[{self.name}] [Step 3/4] Failed: {e}", exc_info=True)

            # === 任务 4: 别名提取 (Alias Extraction) ===
            # 识别用户和实体的别名映射，存入 Alias Vector DB
            t4_start = time.time()
            logger.info(f"[{self.name}] [Step 4/4] 提取实体别名...")
            alias_prompt = ALIAS_EXTRACTION_PROMPT.format(script=script)

            try:
                alias_response = self.llm.chat([{"role": "user", "content": alias_prompt}])
                if alias_response:
                    aliases = extract_json(alias_response)
                    if isinstance(aliases, list):
                        count = 0
                        for item in aliases:
                            alias = item.get("alias")
                            target = item.get("target")
                            if alias and target:
                                self.memory.save_alias(alias, target)
                                count += 1
                        if count > 0:
                            logger.info(f"[{self.name}] [Step 4/4] Done. Updated {count} aliases. (Took {time.time() - t4_start:.2f}s)")
                        else:
                            logger.info(f"[{self.name}] [Step 4/4] Done. No new aliases. (Took {time.time() - t4_start:.2f}s)")
                    else:
                        logger.warning(f"[{self.name}] [Step 4/4] Failed: Response is not a list")
            except Exception as e:
                logger.error(f"[{self.name}] [Step 4/4] Failed: {e}", exc_info=True)

            return diary_response
            
        except Exception as e:
            logger.error(f"[{self.name}] [ERROR] 记忆压缩流程异常: {e}", exc_info=True)
            
        finally:
            # [Fix] 无论成功失败，强制持久化所有记忆
            logger.info(f"[{self.name}] [FINALLY] 正在强制持久化所有记忆...")
            t_save = time.time()
            self.memory.force_save_all()
            logger.info(f"[{self.name}] [FINALLY] 刷盘完成 (Took {time.time() - t_save:.2f}s). Total Cycle Time: {time.time() - start_time:.2f}s")


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
                            logger.info(f"[{self.name}] [S-Brain] 新增深度记忆 ({cat}): {content}")
                            
                # 4. Evolution
                if "evolution_request" in parsed_data:
                    ev_req = parsed_data["evolution_request"]
                    logger.info(f"[{self.name}] [Evolution] S脑渴望进化: {ev_req}")
                    
                # 5. Proactive Instruction [New]
                if "proactive_instruction" in parsed_data:
                    proactive_instruction = parsed_data["proactive_instruction"]
                    logger.info(f"[{self.name}] [Proactive] 生成主动指令: {proactive_instruction}")

            # 原有的基于文本的解析逻辑 (Legacy Fallback) 可以移除了，或者保留作为兜底
            # 鉴于我们已经全面拥抱 JSON，直接使用 extract_json 结果即可
            
            # 返回结果 (Suggestion 用于注入 Driver, Delta 用于更新心智, Instruction 用于主动触发)
            return suggestion, delta, proactive_instruction # 修改了返回值签名
            
        except Exception as e:
            logger.error(f"[{self.name}] 周期分析异常: {e}", exc_info=True)
            return None, None, None

    # 保留旧接口以兼容（或者直接废弃）
    def analyze(self, current_input):
        return self.analyze_cycle()
