import time
import concurrent.futures
import json
from xingchen.config.settings import settings
from xingchen.utils.logger import logger
from xingchen.utils.json_parser import extract_json
from xingchen.config.prompts import (
    DIARY_GENERATION_PROMPT,
    FACT_EXTRACTION_PROMPT,
    COGNITIVE_GRAPH_PROMPT,
    ALIAS_EXTRACTION_PROMPT,
    AUTONOMOUS_LEARNING_TRIGGER_PROMPT,
    GRAPH_EXTRACTION_PROMPT
)
from xingchen.tools.registry import tool_registry
from xingchen.memory.services.orchestrator import orchestrator


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
            future_classify = executor.submit(self._classify_to_hierarchy, script)  
            
            futures = {
                future_diary: "Creative Diary",
                future_facts: "Fact Extraction",
                future_graph: "Cognitive Graph",
                future_alias: "Alias Extraction",
                future_learning: "Autonomous Learning Trigger",
                future_classify: "Hierarchical Classification"
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
        层级记忆分类 (Hierarchical Classification)
        将对话归类到话题层级结构
        """
        try:
            result = orchestrator.classify_compressed_memory(script)
            logger.info(f"[Compressor] 层级分类结果: {result}")
            return result
        except Exception as e:
            logger.warning(f"[Compressor] 层级分类失败: {e}")
            return None

    def generate_creative_diary(self, current_psyche, time_context, script):
        """任务 1: 生成 AI 日记"""
        prompt = DIARY_GENERATION_PROMPT.format(
            current_psyche=current_psyche,
            time_context=time_context,
            script=script
        )
        response_obj = self.llm.chat([{"role": "user", "content": prompt}])
        if response_obj:
            content = response_obj.content
            self.memory.write_diary_entry(content)
            return content
        return None

    def extract_facts(self, script):
        """任务 2: 事实提取"""
        prompt = FACT_EXTRACTION_PROMPT.format(script=script)
        response_obj = self.llm.chat([{"role": "user", "content": prompt}])
        if response_obj:
            content = response_obj.choices[0].message.content
            if content and content.strip() != "None":
                facts = content.strip().split("\n")
                for fact in facts:
                    if fact.strip():
                        self.memory.add_long_term(fact.strip(), category="fact")
            return content
        return None

    def build_cognitive_graph(self, current_psyche, script):
        """任务 3: 构建认知图谱 (增强版)"""
        prompt = COGNITIVE_GRAPH_PROMPT.format(current_psyche=current_psyche, script=script)
        response_obj = self.llm.chat([{"role": "user", "content": prompt}])
        if response_obj:
            content = response_obj.content
            triplets = extract_json(content)
            if triplets and isinstance(triplets, list):
                for t in triplets:
                    source = t.get("source")
                    target = t.get("target")
                    relation = t.get("relation")
                    if source and target and relation:
                        self.memory.graph_storage.add_triplet(
                            source=source,
                            relation=relation,
                            target=target,
                            weight=t.get("weight", 0.8),
                            relation_type=t.get("relation_type", "general"),
                            meta={
                                "emotion_tag": t.get("emotion_tag"),
                                "psyche_context": current_psyche
                            }
                        )
            return content
        return None

    def extract_aliases(self, script):
        """任务 4: 别名提取"""
        prompt = ALIAS_EXTRACTION_PROMPT.format(script=script)
        response_obj = self.llm.chat([{"role": "user", "content": prompt}])
        if response_obj:
            content = response_obj.content
            aliases = extract_json(content)
            if aliases and isinstance(aliases, list):
                for a in aliases:
                    alias = a.get("alias")
                    target = a.get("target")
                    if alias and target:
                        self.memory.service.save_alias(alias, target)
            return content
        return None

    def trigger_autonomous_learning(self, script):
        """
        任务 5: 自主学习触发器 (Autonomous Learning)
        分析对话记录，识别未知概念，直接调用 web_search/web_crawl 获取知识。
        """
        prompt = AUTONOMOUS_LEARNING_TRIGGER_PROMPT.format(script=script)
        response_obj = self.llm.chat([{"role": "user", "content": prompt}])
        if not response_obj:
            return
            
        try:
            response = response_obj.content
            logger.info(f"[Compressor] Autonomous Learning Response: {response}") 
            tasks = extract_json(response)
            if not tasks or not isinstance(tasks, list):
                logger.info(f"[Compressor] No learning tasks found or invalid format.")
                return

            for task in tasks:
                query = task.get("query")
                if not query: continue
                
                logger.info(f"[Compressor] 📖 开始自主学习: {query} (原因: {task.get('reason')})")
                
                # 直接调用 web_search 工具获取实时信息
                search_results = tool_registry.execute("web_search", query=query, max_results=3)
                
                if search_results and "Error" not in str(search_results):
                    # 将搜索到的内容存入 Staging 目录，等待下一轮知识内化
                    staging_dir = os.path.join(settings.PROJECT_ROOT, "src", "skills_library", "staging")
                    os.makedirs(staging_dir, exist_ok=True)
                    
                    filename = f"learned_{int(time.time())}_{hash(query)%1000}.md"
                    filepath = os.path.join(staging_dir, filename)
                    
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(f"--- \ntype: knowledge_staging\nquery: {query}\nreason: {task.get('reason')}\ntimestamp: {time.time()}\n---\n\n")
                        f.write(str(search_results))
                    
                    logger.info(f"[Compressor] ✅ 自主学习完成，已缓存至 Staging: {filepath}")
        except Exception as e:
            logger.error(f"[Compressor] 自主学习触发失败: {e}", exc_info=True)

    def clean_short_term_memory(self):
        """清理短期记忆"""
        self.memory.clear_short_term()
        logger.info("[Compressor] 短期记忆已清空")
