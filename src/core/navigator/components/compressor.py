from src.config.settings.settings import settings
from src.utils.logger import logger
from src.utils.json_parser import extract_json
from src.config.prompts.prompts import (
    DIARY_GENERATION_PROMPT,
    FACT_EXTRACTION_PROMPT,
    COGNITIVE_GRAPH_PROMPT,
    ALIAS_EXTRACTION_PROMPT,
    AUTONOMOUS_LEARNING_TRIGGER_PROMPT # [New]
)
import time
import concurrent.futures
from src.tools.registry import tool_registry # [New] 用于直接调用工具
from src.memory.services.memory_orchestrator import memory_orchestrator  # [New] 层级分类

class Compressor:
    """
    记忆压缩师 (Compressor)
    职责：执行具体的记忆压缩原子任务
    """
    def __init__(self, llm, memory):
        self.llm = llm
        self.memory = memory

    def run_compression_tasks_parallel(self, current_psyche, time_context, script):
        """并行执行所有压缩任务"""
        logger.info(f"[Compressor] 🚀 启动并行记忆压缩 (6路并发)...")
        start_time = time.time()
        
        diary_response = None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            # 提交任务
            future_diary = executor.submit(self.generate_creative_diary, current_psyche, time_context, script)
            future_facts = executor.submit(self.extract_facts, script)
            future_graph = executor.submit(self.build_cognitive_graph, current_psyche, script)
            future_alias = executor.submit(self.extract_aliases, script)
            future_learning = executor.submit(self.trigger_autonomous_learning, script)
            future_classify = executor.submit(self._classify_to_hierarchy, script)  # [New] 层级分类
            
            futures = {
                future_diary: "Creative Diary",
                future_facts: "Fact Extraction",
                future_graph: "Cognitive Graph",
                future_alias: "Alias Extraction",
                future_learning: "Autonomous Learning Trigger",
                future_classify: "Hierarchical Classification"  # [New]
            }
            
            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    if future == future_diary:
                        diary_response = result
                    logger.info(f"[Compressor] ✅ {name} 完成")
                except Exception as e:
                    logger.error(f"[Compressor] ❌ {name} 失败: {e}", exc_info=True)
                    
        logger.info(f"[Compressor] 并行压缩完成，耗时: {time.time() - start_time:.2f}s")
        return diary_response
    
    def _classify_to_hierarchy(self, script: str):
        """
        任务 6: 层级记忆分类 (Hierarchical Classification)
        将对话归类到话题层级结构
        """
        try:
            result = memory_orchestrator.classify_compressed_memory(script)
            logger.info(f"[Compressor] 层级分类结果: {result}")
            return result
        except Exception as e:
            logger.warning(f"[Compressor] 层级分类失败: {e}")
            return None

    # ... (generate_creative_diary, extract_facts, build_cognitive_graph, extract_aliases 保持不变) ...

    def trigger_autonomous_learning(self, script):
        """
        任务 5: 自主学习触发器 (Autonomous Learning)
        分析对话记录，识别未知概念，直接调用 web_search/web_crawl 获取知识。
        """
        prompt = AUTONOMOUS_LEARNING_TRIGGER_PROMPT.format(script=script)
        
        # 使用 json mode (假设 LLM 支持，或依靠 prompt 约束)
        response = self.llm.chat([{"role": "user", "content": prompt}])
        if not response:
            return
            
        try:
            logger.info(f"[Compressor] Autonomous Learning Response: {response}") # [Debug]
            tasks = extract_json(response)
            if not tasks or not isinstance(tasks, list):
                logger.info(f"[Compressor] No learning tasks found or invalid format.")
                return

            for task in tasks:
                query = task.get("query")
                reason = task.get("reason")
                if not query: continue
                
                logger.info(f"[Compressor] 🧠 S脑发现知识盲区: '{query}' (原因: {reason})")
                
                # 直接调用 web_search 工具 (S脑自主行动!)
                # 注意：这里我们使用 web_search 而不是 web_crawl，因为 search 比较快且通用
                # 并且 web_search (在本项目的实现中) 通常会返回摘要
                # 如果需要深度学习，可以调用 web_crawl
                
                # 检查工具是否可用
                # [Fix] 使用公开的 get_tool() 方法代替访问私有 _tools
                
                try:
                    logger.info(f"[Compressor] 🚀 S脑正在自主搜索: {query} ...")
                    # 确保 web_search 工具已注册
                    if tool_registry.get_tool("web_search") is None:
                         # 尝试动态加载（如果尚未加载）
                         from src.tools.builtin import web_tools
                    
                    result = tool_registry.execute("web_search", query=query, max_results=3)
                    
                    # 将结果直接保存到 Staging 区 (模拟 Crawl 的效果，或者创建专门的 Knowledge Note)
                    # 为了复用 KnowledgeIntegrator，我们将结果保存为 .md 文件
                    self._save_search_result_to_staging(query, result)
                    
                except Exception as e:
                    logger.error(f"[Compressor] S脑自主搜索失败: {e}", exc_info=True) # [Debug]
                    
        except Exception as e:
            logger.warning(f"[Compressor] 自主学习触发分析出错: {e}")

    def _save_search_result_to_staging(self, query, content):
        """将搜索结果保存到 staging 区，供后续 KnowledgeIntegrator 内化"""
        import os
        from datetime import datetime
        
        staging_dir = os.path.join(settings.PROJECT_ROOT, "storage", "knowledge_staging")
        os.makedirs(staging_dir, exist_ok=True)
        
        filename = f"s_brain_search_{int(time.time())}.md"
        filepath = os.path.join(staging_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# S-Brain Autonomous Search: {query}\n")
            f.write(f"# Date: {datetime.now().isoformat()}\n\n")
            f.write(str(content))
            
        logger.info(f"[Compressor] ✅ S脑搜索结果已保存至 Staging: {filename}")

    def generate_creative_diary(self, current_psyche, time_context, script):
        """任务 1: 生成趣味日记 (Pure Logic)"""
        diary_prompt = DIARY_GENERATION_PROMPT.format(
            current_psyche=current_psyche,
            time_context=time_context,
            script=script
        )

        diary_response = self.llm.chat([{"role": "user", "content": diary_prompt}])
        if diary_response:
            self.memory.write_diary_entry(diary_response)
        return diary_response

    def extract_facts(self, script):
        """任务 2: 提取工程记忆 (事实) - Pure Logic"""
        fact_prompt = FACT_EXTRACTION_PROMPT.format(script=script)
        
        fact_response = self.llm.chat([{"role": "user", "content": fact_prompt}])
        if fact_response and "None" not in fact_response:
            # 移除 markdown 代码块标记
            clean_fact = fact_response.replace("```text", "").replace("```", "").strip()
            lines = clean_fact.split('\n')
            count = 0
            for line in lines:
                line = line.strip().strip('- ')
                if line:
                    self.memory.add_long_term(line, category="fact")
                    count += 1
            # 注意：不在此处 commit，由 Navigator 统一保存
            return count
        return 0

    def build_cognitive_graph(self, current_psyche, script):
        """任务 3: 构建认知图谱 - Pure Logic"""
        graph_prompt = COGNITIVE_GRAPH_PROMPT.format(
            current_psyche=current_psyche,
            script=script
        )
        
        graph_response = self.llm.chat([{"role": "user", "content": graph_prompt}])
        if graph_response:
            triplets = extract_json(graph_response)
            
            if isinstance(triplets, list):
                count = 0
                for t in triplets:
                    if all(k in t for k in ["source", "target", "relation"]):
                        meta_data = {
                            "psyche_context": current_psyche,
                            "emotion_tag": t.get("emotion_tag", "neutral")
                        }
                        
                        self.memory.add_triplet(
                            source=t["source"],
                            relation=t["relation"],
                            target=t["target"],
                            weight=t.get("weight", 1.0),
                            relation_type=t.get("relation_type", "general"),
                            meta=meta_data
                        )
                        count += 1
                # 不在此处 save_graph
                return count
        return 0

    def extract_aliases(self, script):
        """任务 4: 提取实体别名 - Pure Logic"""
        alias_prompt = ALIAS_EXTRACTION_PROMPT.format(script=script)

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
                return count
        return 0

    def clean_short_term_memory(self):
        """清理短期记忆，保留最近上下文"""
        try:
            # 获取最近 5 条 (使用 Facade 属性)
            recent = self.memory.short_term[-5:]
            # 清空 (使用 Facade 方法)
            self.memory.clear_short_term()
            # 加回最近 5 条 (使用 Facade 方法，会正确触发 WAL)
            for entry in recent:
                self.memory.add_short_term(entry.role, entry.content)
            logger.info(f"[Compressor] 短期记忆已清理 (保留 {len(recent)} 条上下文)。")
        except Exception as e:
            logger.error(f"[Compressor] 短期记忆清理失败: {e}", exc_info=True)
