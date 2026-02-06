from src.config.settings.settings import settings
from src.utils.logger import logger
from src.utils.json_parser import extract_json
from src.config.prompts.prompts import (
    DIARY_GENERATION_PROMPT,
    FACT_EXTRACTION_PROMPT,
    COGNITIVE_GRAPH_PROMPT,
    ALIAS_EXTRACTION_PROMPT
)
import time
import concurrent.futures

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
        logger.info(f"[Compressor] 🚀 启动并行记忆压缩 (4路并发)...")
        start_time = time.time()
        
        diary_response = None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # 提交任务
            future_diary = executor.submit(self.generate_creative_diary, current_psyche, time_context, script)
            future_facts = executor.submit(self.extract_facts, script)
            future_graph = executor.submit(self.build_cognitive_graph, current_psyche, script)
            future_alias = executor.submit(self.extract_aliases, script)
            
            futures = {
                future_diary: "Creative Diary",
                future_facts: "Fact Extraction",
                future_graph: "Cognitive Graph",
                future_alias: "Alias Extraction"
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
