import os
import yaml
import time
from typing import List, Dict, Optional
from src.memory.memory_core import Memory
from src.utils.logger import logger

from src.tools.registry import tool_registry, ToolTier

class LibraryManager:
    """
    技能图书馆管理员 (The Librarian)
    负责：
    1. 技能编目 (Cataloging): 扫描 SKILL.md，存入 ChromaDB
    2. 技能检索 (Retrieval): 根据 Query 查找相关技能
    3. 技能借阅 (Checkout): 读取 SKILL.md 内容
    4. MCP 管理 (MCP Manager): 加载和管理 MCP 工具
    """
    _instance = None
    
    def __new__(cls, memory: Memory = None):
        if cls._instance is None:
            cls._instance = super(LibraryManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, memory: Memory = None):
        # 允许 lazy injection，避免循环依赖
        if memory:
            self.memory = memory
            self.collection = memory.get_skill_collection()
        else:
            self.memory = None
            self.collection = None
            
        self.root_dir = os.path.join("src", "skills_library")

    def load_mcp_tool(self, config: Dict) -> bool:
        """
        加载 MCP 工具
        :param config: MCP 配置 (command, args, env)
        :return: Success
        """
        # [TODO] 真正的 MCP 加载逻辑需要集成 mcp-python SDK
        # 这里暂时模拟注册过程，将 MCP 工具注册到 ToolRegistry
        try:
            tool_name = f"mcp_{int(time.time())}"
            print(f"[Library] Loading MCP tool: {config}")
            
            # 动态注册一个代理函数
            # 注意：实际 MCP 需要复杂的 Client/Server 通信，这里仅作为占位符
            # 在完整实现中，这里应该启动 MCP Client 并连接到 Server
            
            @tool_registry.register(
                name=tool_name,
                description=f"MCP Tool loaded from {config.get('command')}",
                tier=ToolTier.SLOW
            )
            def mcp_proxy(**kwargs):
                return f"MCP Tool executed with {kwargs} (Mock)"
                
            return True
        except Exception as e:
            logger.error(f"[Library] Failed to load MCP tool: {e}", exc_info=True)
            return False

    def set_memory(self, memory: Memory):
        self.memory = memory
        self.collection = memory.get_skill_collection()

    def scan_and_index(self):
        """扫描 src/skills_library 下所有的 SKILL.md 并入库"""
        if not self.collection:
            print("[Library] ❌ Memory not initialized, cannot index.")
            return

        print("[Library] 🔍 Scanning skills library...")
        
        # 1. 获取数据库中现有的所有 ID
        existing_ids = set()
        try:
            # get() 不带参数默认返回所有 ID
            db_data = self.collection.get()
            if db_data and 'ids' in db_data:
                existing_ids = set(db_data['ids'])
        except Exception as e:
            logger.error(f"[Library] Failed to fetch existing IDs: {e}", exc_info=True)

        found_skills = []
        
        # 2. 遍历目录，解析所有技能
        for root, dirs, files in os.walk(self.root_dir):
            if "SKILL.md" in files:
                skill_path = os.path.join(root, "SKILL.md")
                skill_data = self._parse_skill_file(skill_path)
                if skill_data:
                    found_skills.append(skill_data)
        
        found_ids = set(s['id'] for s in found_skills)
        
        # 3. 计算增量
        new_ids = found_ids - existing_ids
        deleted_ids = existing_ids - found_ids
        
        # 4. 执行更新 (Upsert 所有发现的技能，确保内容最新)
        if found_skills:
            ids = [s['id'] for s in found_skills]
            documents = [s['document'] for s in found_skills]
            metadatas = [s['metadata'] for s in found_skills]
            
            try:
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                print(f"[Library] ✅ Upserted {len(found_skills)} skills.")
            except Exception as e:
                print(f"[Library] Batch upsert failed: {e}")

        # 5. 执行清理 (删除已不存在的技能)
        if deleted_ids:
            try:
                self.collection.delete(ids=list(deleted_ids))
                print(f"[Library] 🗑️ Cleaned up {len(deleted_ids)} stale skills: {deleted_ids}")
            except Exception as e:
                print(f"[Library] Cleanup failed: {e}")

        # 6. 记录新技能到日记
        if new_ids and self.memory:
            new_skill_names = [s['metadata']['name'] for s in found_skills if s['id'] in new_ids]
            if new_skill_names:
                diary_content = f"今天我学会了新技能: {', '.join(new_skill_names)}。感觉自己变强了呢！"
                self.memory.write_diary_entry(diary_content)
                print(f"[Library] 📝 Logged new skills to diary: {new_skill_names}")

    def _parse_skill_file(self, file_path: str) -> Optional[Dict]:
        """解析单个 SKILL.md，返回数据结构而不直接入库"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.startswith("---"):
                print(f"[Library] ⚠️ Invalid SKILL.md format (no frontmatter): {file_path}")
                return None

            parts = content.split("---", 2)
            if len(parts) < 3:
                print(f"[Library] ⚠️ Invalid SKILL.md format: {file_path}")
                return None
                
            frontmatter_raw = parts[1]
            try:
                meta = yaml.safe_load(frontmatter_raw)
            except yaml.YAMLError as e:
                print(f"[Library] ⚠️ YAML parse error in {file_path}: {e}")
                return None

            name = meta.get("name")
            desc = meta.get("description")
            
            if not name or not desc:
                print(f"[Library] ⚠️ Missing name/description in {file_path}")
                return None

            # 生成 ID
            rel_path = os.path.relpath(file_path, self.root_dir)
            skill_id = rel_path.replace(os.sep, ".").replace(".SKILL.md", "")
            
            # 构造向量文本
            document = f"Skill: {name}\nDescription: {desc}"
            
            return {
                "id": skill_id,
                "document": document,
                "metadata": {
                    "name": name, 
                    "description": desc, 
                    "path": file_path, 
                    "id": skill_id
                }
            }
            
        except Exception as e:
            print(f"[Library] Failed to parse {file_path}: {e}")
            return None

    def search_skills(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        语义检索技能
        返回: [{"name":..., "description":..., "path":...}, ...]
        """
        if not self.collection:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            skills = []
            if results['ids']:
                for i, doc_id in enumerate(results['ids'][0]):
                    meta = results['metadatas'][0][i]
                    skills.append(meta)
            return skills
            
        except Exception as e:
            print(f"[Library] Search failed: {e}")
            return []

    def checkout_skill(self, file_path: str) -> str:
        """读取技能内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading skill file: {e}"

# Global Singleton Instance
library_manager = LibraryManager()
