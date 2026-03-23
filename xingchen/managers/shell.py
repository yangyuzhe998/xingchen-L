import os
import uuid
import time
from typing import List, Dict, Optional
from xingchen.memory.facade import Memory
from xingchen.config.settings import settings
from xingchen.utils.logger import logger


class ShellManager:
    """
    RAG-Powered Smart Shell Manager
    负责：
    1. Command Docs Management (Static Knowledge): 静态命令文档库
    2. Command Cases Management (Dynamic Experience Replay): 动态执行案例库 (带信任评分)
    3. Retrieval (RAG): 混合检索上下文
    """
    _instance = None
    
    def __new__(cls, memory: Memory = None):
        if cls._instance is None:
            cls._instance = super(ShellManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, memory: Memory = None):
        # 允许 lazy injection
        if memory:
            self.set_memory(memory)
        else:
            self.memory = None
            self.docs_collection = None
            self.cases_collection = None
            
        self.docs_root_dir = os.path.join(settings.PROJECT_ROOT, "src", "skills_library", "command_docs")

    def set_memory(self, memory: Memory):
        self.memory = memory
        self.docs_collection = memory.get_command_docs_collection()
        self.cases_collection = memory.get_command_cases_collection()

    def scan_and_index(self):
        """扫描 src/skills_library/command_docs 下所有的 .md 并入库"""
        if not self.docs_collection:
            logger.error("[ShellManager] ❌ Collection not initialized.")
            return

        logger.info("[ShellManager] 🔍 Scanning command docs...")
        
        if not os.path.exists(self.docs_root_dir):
            os.makedirs(self.docs_root_dir)
            return
        
        for root, dirs, files in os.walk(self.docs_root_dir):
            for file in files:
                if file.endswith(".md"):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 简单假设文件名就是命令名 (e.g. git_log.md -> git log)
                        command_name = os.path.splitext(file)[0].replace("_", " ")
                        
                        self.add_command_doc(command_name, content, source="file")
                        
                    except Exception as e:
                        logger.error(f"[ShellManager] Failed to index {file}: {e}", exc_info=True)

    def add_command_doc(self, command_name: str, content: str, source: str = "manual"):
        """添加静态命令文档"""
        if not self.docs_collection: 
            logger.error("[ShellManager] ❌ Collection not initialized.")
            return False
        
        # 生成唯一ID，允许同一命令有多个文档片段
        doc_id = f"doc_{command_name}_{uuid.uuid4().hex[:8]}"
        try:
            self.docs_collection.upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[{"command": command_name, "source": source, "type": "doc"}]
            )
            logger.info(f"[ShellManager] ✅ Added command doc: {command_name}")
            return True
        except Exception as e:
            logger.error(f"[ShellManager] ❌ Failed to add doc: {e}", exc_info=True)
            return False

    def add_command_case(self, command: str, scenario: str, outcome: str, trust_score: float = 0.5):
        """
        添加动态执行案例 (Experience Replay)
        :param command: 执行的命令
        :param scenario: 场景描述/用户意图
        :param outcome: 执行结果摘要
        :param trust_score: 初始信任值 (0.0 - 1.0)
        """
        if not self.cases_collection: 
            logger.error("[ShellManager] ❌ Collection not initialized.")
            return False
        
        case_id = f"case_{uuid.uuid4().hex[:8]}"
        try:
            self.cases_collection.upsert(
                ids=[case_id],
                documents=[f"Scenario: {scenario}\nCommand: {command}\nOutcome: {outcome}"],
                metadatas=[{
                    "command": command,
                    "scenario": scenario,
                    "trust_score": trust_score,
                    "timestamp": time.time(),
                    "type": "case"
                }]
            )
            logger.info(f"[ShellManager] ✅ Added command case: {command}")
            return True
        except Exception as e:
            logger.error(f"[ShellManager] ❌ Failed to add case: {e}", exc_info=True)
            return False

    def get_context(self, query: str, top_k: int = 3) -> str:
        """
        检索混合上下文 (Docs + Cases)
        """
        if not self.docs_collection or not self.cases_collection:
            return ""
            
        context_parts = []
        
        # 1. 检索文档
        try:
            doc_res = self.docs_collection.query(query_texts=[query], n_results=top_k)
            if doc_res['ids']:
                context_parts.append("### Relevant Documentation")
                for doc in doc_res['documents'][0]:
                    context_parts.append(doc)
        except Exception as e:
            logger.error(f"[ShellManager] Doc search failed: {e}")

        # 2. 检索案例
        try:
            case_res = self.cases_collection.query(query_texts=[query], n_results=top_k)
            if case_res['ids']:
                context_parts.append("\n### Past Experiences (Experience Replay)")
                for case in case_res['documents'][0]:
                    context_parts.append(case)
        except Exception as e:
            logger.error(f"[ShellManager] Case search failed: {e}")

        return "\n".join(context_parts)


# Global Singleton Instance
shell_manager = ShellManager()
