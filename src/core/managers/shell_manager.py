import os
import uuid
import time
from typing import List, Dict, Optional
from ...memory.memory_core import Memory
from ...config.settings.settings import settings
from ...utils.logger import logger

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
                        
                        # 简单假设文件名就是命令名 (e.g. git_status.md -> git status)
                        command_name = os.path.splitext(file)[0].replace("_", " ")
                        
                        self.add_command_doc(command_name, content, source="file")
                        
                    except Exception as e:
                        print(f"[ShellManager] Failed to index {file}: {e}")

    def add_command_doc(self, command_name: str, content: str, source: str = "manual"):
        """添加静态命令文档"""
        if not self.docs_collection: 
            print("[ShellManager] ❌ Collection not initialized.")
            return False
        
        # 生成唯一ID，允许同一命令有多个文档片段
        doc_id = f"doc_{command_name}_{uuid.uuid4().hex[:8]}"
        try:
            self.docs_collection.upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[{"command": command_name, "source": source, "type": "doc"}]
            )
            print(f"[ShellManager] ✅ Added command doc: {command_name}")
            return True
        except Exception as e:
            print(f"[ShellManager] ❌ Failed to add doc: {e}")
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
        
        # 文档内容包含场景和命令，以便检索
        document = f"Scenario: {scenario}\nCommand: {command}\nOutcome: {outcome}"
        
        try:
            self.cases_collection.add(
                ids=[case_id],
                documents=[document],
                metadatas=[{
                    "command": command,
                    "trust_score": trust_score,
                    "timestamp": time.time(),
                    "type": "case"
                }]
            )
            print(f"[ShellManager] 📝 Added command case: {command} (Trust: {trust_score})")
            return True
        except Exception as e:
            print(f"[ShellManager] ❌ Failed to add case: {e}")
            return False

    def retrieve_context(self, query: str, top_k: int = 3) -> Dict[str, List[str]]:
        """
        RAG 核心：检索文档和案例
        """
        context = {
            "docs": [],
            "cases": []
        }
        
        if self.docs_collection:
            try:
                res = self.docs_collection.query(query_texts=[query], n_results=top_k)
                if res and res['documents']:
                    context["docs"] = res['documents'][0]
            except Exception as e:
                print(f"[ShellManager] Doc retrieval failed: {e}")

        if self.cases_collection:
            try:
                # 检索案例
                res = self.cases_collection.query(query_texts=[query], n_results=top_k)
                if res and res['documents'] and res['metadatas']:
                    docs = res['documents'][0]
                    metas = res['metadatas'][0]
                    
                    # 过滤信任值过低的案例 (例如 < 0.3)
                    valid_cases = []
                    for doc, meta in zip(docs, metas):
                        trust = meta.get("trust_score", 0.0)
                        if trust >= 0.3:
                            valid_cases.append(f"[Trust: {trust:.2f}] {doc}")
                        else:
                            # 可以在这里触发一个“遗忘”机制，或者仅过滤
                            pass
                            
                    context["cases"] = valid_cases
            except Exception as e:
                print(f"[ShellManager] Case retrieval failed: {e}")
                
        return context

    def update_case_trust(self, case_id: str, delta: float):
        """
        更新案例信任值 (Reinforcement Learning signal)
        """
        # [TODO] 需要先检索 id 对应的 metadata，然后更新
        # ChromaDB 的 update 需要传入全量 metadata，所以比较麻烦
        # 暂时留空，后续实现
        pass

# Global Instance
shell_manager = ShellManager()
