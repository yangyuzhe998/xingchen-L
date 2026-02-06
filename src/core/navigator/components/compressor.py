from ....config.settings.settings import settings
from ....utils.logger import logger
from ....utils.json_parser import extract_json
from ....config.prompts.prompts import (
    DIARY_GENERATION_PROMPT,
    FACT_EXTRACTION_PROMPT,
    COGNITIVE_GRAPH_PROMPT,
    ALIAS_EXTRACTION_PROMPT
)
import time

class Compressor:
    """
    记忆压缩师 (Compressor)
    职责：执行具体的记忆压缩原子任务
    """
    def __init__(self, llm, memory):
        self.llm = llm
        self.memory = memory

    def generate_creative_diary(self, current_psyche, time_context, script):
        """任务 1: 生成趣味日记"""
        t1_start = time.time()
        logger.info(f"[Compressor] [1/4] 生成趣味日记...")
        diary_prompt = DIARY_GENERATION_PROMPT.format(
            current_psyche=current_psyche,
            time_context=time_context,
            script=script
        )

        diary_response = None
        try:
            diary_response = self.llm.chat([{"role": "user", "content": diary_prompt}])
            if diary_response:
                self.memory.write_diary_entry(diary_response)
            logger.info(f"[Compressor] [1/4] 完成 ({time.time() - t1_start:.2f}s)")
        except Exception as e:
            logger.error(f"[Compressor] [1/4] 失败: {e}", exc_info=True)
        return diary_response

    def extract_facts(self, script):
        """任务 2: 提取工程记忆 (事实)"""
        t2_start = time.time()
        logger.info(f"[Compressor] [2/4] 提取工程记忆...")
        fact_prompt = FACT_EXTRACTION_PROMPT.format(script=script)
        
        try:
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
                logger.info(f"[Compressor] [2/4] 提取 {count} 条事实 ({time.time() - t2_start:.2f}s)")
                
                # [Optimization] 立即提交长期记忆
                self.memory.commit_long_term()
                
            else:
                logger.info(f"[Compressor] [2/4] 无新事实 ({time.time() - t2_start:.2f}s)")
                
        except Exception as e:
            logger.error(f"[Compressor] [2/4] 失败: {e}", exc_info=True)

    def build_cognitive_graph(self, current_psyche, script):
        """任务 3: 构建认知图谱"""
        t3_start = time.time()
        logger.info(f"[Compressor] [3/4] 构建认知图谱...")
        graph_prompt = COGNITIVE_GRAPH_PROMPT.format(
            current_psyche=current_psyche,
            script=script
        )
        
        try:
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
                    logger.info(f"[Compressor] [3/4] 更新 {count} 条关系 ({time.time() - t3_start:.2f}s)")
                    
                    # [Optimization] 立即提交认知图谱
                    self.memory.save_graph()
                    
                else:
                    logger.warning(f"[Compressor] [3/4] 格式错误 (非列表)")
        except Exception as e:
            logger.error(f"[Compressor] [3/4] 失败: {e}", exc_info=True)

    def extract_aliases(self, script):
        """任务 4: 提取实体别名"""
        t4_start = time.time()
        logger.info(f"[Compressor] [4/4] 提取实体别名...")
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
                        logger.info(f"[Compressor] [4/4] 更新 {count} 个别名 ({time.time() - t4_start:.2f}s)")
                    else:
                        logger.info(f"[Compressor] [4/4] 无新别名 ({time.time() - t4_start:.2f}s)")
                else:
                    logger.warning(f"[Compressor] [4/4] 格式错误 (非列表)")
        except Exception as e:
            logger.error(f"[Compressor] [4/4] 失败: {e}", exc_info=True)

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
