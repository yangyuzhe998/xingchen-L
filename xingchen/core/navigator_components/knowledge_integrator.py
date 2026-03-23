import os
import shutil
import glob
from xingchen.utils.logger import logger
from xingchen.utils.json_parser import extract_json
from xingchen.config.settings import settings
from xingchen.config.prompts import KNOWLEDGE_INTERNALIZATION_PROMPT
from xingchen.memory.storage.knowledge_db import knowledge_db


class KnowledgeIntegrator:
    """
    知识内化器 (Knowledge Integrator)
    职责：扫描 Staging 区，读取文档，提炼知识与经验，存入长期记忆。
    """
    def __init__(self, llm, memory):
        self.llm = llm
        self.memory = memory
        self.staging_dir = os.path.join(settings.DATA_DIR, "knowledge_staging")
        self.archive_dir = os.path.join(settings.DATA_DIR, "knowledge_archive")
        
        # 确保目录存在
        os.makedirs(self.staging_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)

    def scan_and_process(self, limit=1):
        """
        扫描 Staging 区并处理 N 个文档
        :param limit: 每次处理的文件数量上限 (防止 S脑 过载)
        :return: 处理结果摘要
        """
        # 获取所有 .md 文件
        files = glob.glob(os.path.join(self.staging_dir, "*.md"))
        if not files:
            return None
            
        processed_count = 0
        results = []
        
        # 按时间排序，优先处理最早的文件 (FIFO)
        files.sort(key=os.path.getmtime)
        
        for file_path in files[:limit]:
            try:
                filename = os.path.basename(file_path)
                logger.info(f"[Integrator] 开始处理文档: {filename}")
                
                # 1. 读取内容
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 截断过长内容 (DeepSeek 支持 32k/64k，但为了效率限制在 10k 字符)
                if len(content) > 10000:
                    content = content[:10000] + "\n...(truncated)..."
                
                # 2. 调用 LLM 进行提炼
                prompt = KNOWLEDGE_INTERNALIZATION_PROMPT.format(document_content=content)
                response_obj = self.llm.chat([{"role": "user", "content": prompt}])
                
                if not response_obj:
                    logger.warning(f"[Integrator] LLM 未返回结果，跳过: {filename}")
                    continue
                
                response = response_obj.content
                parsed_data = extract_json(response)
                if not parsed_data:
                    logger.warning(f"[Integrator] JSON 解析失败，跳过: {filename}")
                    continue
                
                # 3. 存入记忆
                summary = parsed_data.get("summary", "无摘要")
                knowledge_items = parsed_data.get("knowledge", [])
                experience_items = parsed_data.get("experience", [])
                
                # 存入 Knowledge (Facts)
                for item in knowledge_items:
                    # SQLite: 结构化存储，支持精确查询
                    knowledge_db.add_knowledge(
                        content=item,
                        category="fact",
                        source=f"s_brain:{filename}",
                        confidence=0.8
                    )
                    # ChromaDB: 向量存储，支持语义搜索
                    self.memory.add_long_term(item, category="knowledge")
                    
                # 存入 Experience (Rules)
                for item in experience_items:
                    # 经验主要用于语义搜索，只存 ChromaDB
                    self.memory.add_long_term(item, category="experience")
                
                logger.info(f"[Integrator] ✅ 内化完成: {len(knowledge_items)} 知识, {len(experience_items)} 经验。")
                
                # 4. 归档文件
                shutil.move(file_path, os.path.join(self.archive_dir, filename))
                
                processed_count += 1
                results.append(f"Processed {filename}: {summary}")
            except Exception as e:
                logger.error(f"[Integrator] 处理文档 {file_path} 失败: {e}", exc_info=True)
                
        return "\n".join(results) if results else None
