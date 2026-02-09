import json
import logging
import re
from typing import List, Dict, Any
from src.core.navigator.driver import Driver
from src.core.navigator.reasoner import Reasoner
from src.memory.storage.knowledge_db import KnowledgeDB
from src.config.prompts.prompts import GRAPH_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

class GraphExtractor:
    """
    负责从文本中提取图谱节点和边 (Phase 7)
    使用 S-Brain (Reasoner) 进行深度提取
    """
    
    def __init__(self, reasoner: Reasoner, knowledge_db: KnowledgeDB, llm_client: Any): # Added llm_client
        self.reasoner = reasoner
        self.knowledge_db = knowledge_db
        self.llm_client = llm_client # Store llm_client
        
    def extract(self, text: str) -> Dict[str, List[Dict]]:
        """
        执行图谱提取
        :param text: 输入文本 (S脑总结或对话片段)
        :return: 包含 'nodes' 和 'edges' 的字典
        """
        if not text or len(text) < 10:
            return {"nodes": [], "edges": []}

        logger.info(f"[GraphExtractor] Starting extraction for text length: {len(text)}")

        # 1. 构造 Prompt
        prompt = GRAPH_EXTRACTION_PROMPT.format(input_text=text)

        # 2. 调用 LLM
        try:
            response = self.llm_client.one_chat(prompt)
            # 3. 解析结果
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"[GraphExtractor] 提取失败: {e}")
            return {"nodes": [], "edges": []}
            
    def extract_and_store(self, content: str, context: str = "") -> Dict[str, int]:
        """
        提取并存储图谱数据
        :param content: 需要提取的文本内容 (Dialogue / Memory)
        :param context: 额外的上下文信息
        :return: 统计信息 {"nodes": N, "edges": M}
        """
        if not content:
            return {"nodes": 0, "edges": 0}
            
        logger.info(f"[GraphExtractor] Starting extraction for content length: {len(content)}")
        
        # 1. 调用 S-Brain 提取 (现在通过 extract 方法)
        try:
            # Combine content and context for extraction
            full_text = f"Context: {context}\nText: {content}" if context else content
            extraction_result = self.extract(full_text)
        except Exception as e:
            logger.error(f"[GraphExtractor] Graph extraction failed: {e}")
            return {"nodes": 0, "edges": 0}
            
        # 2. 存入数据库
        nodes_count = 0
        edges_count = 0
        
        # 存储节点
        for node in extraction_result.get("nodes", []):
            if self.knowledge_db.add_node(
                name=node["name"],
                type=node.get("type", "concept"),
                weight=node.get("weight", 1.0)
            ):
                nodes_count += 1
                
        # 存储边
        for edge in extraction_result.get("edges", []):
            if self.knowledge_db.add_edge(
                source=edge["source"],
                target=edge["target"],
                relation=edge.get("relation", "RELATED_TO"),
                weight=edge.get("weight", 1.0)
            ):
                edges_count += 1
                
        logger.info(f"[GraphExtractor] Extraction complete. Added {nodes_count} nodes, {edges_count} edges.")
        return {"nodes": nodes_count, "edges": edges_count}
    
    def _parse_response(self, response: str) -> Dict[str, List[Dict]]:
        """
        解析 LLM 的 JSON 输出
        """
        try:
            # 尝试提取 Markdown 代码块中的 JSON
            match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                # 尝试直接解析 (如果 LLM 只返回了 JSON)
                json_str = response.strip()

            data = json.loads(json_str)
            
            # 验证结构
            if "nodes" not in data: data["nodes"] = []
            if "edges" not in data: data["edges"] = []
            
            return data

        except json.JSONDecodeError:
            logger.warning(f"[GraphExtractor] JSON 解析失败. Response: {response[:100]}...")
            return {"nodes": [], "edges": []}
    
    def _invoke_s_brain(self, content: str, context: str) -> Dict[str, Any]:
        """
        构造 Prompt 让 S-Brain 提取实体关系
        """
        system_prompt = """
        You are an expert Knowledge Graph Engineer. Your task is to extract meaningful Entities (Nodes) and Relationships (Edges) from the given text.
        
        output format must be strictly JSON:
        {
            "nodes": [
                {"name": "EntityName", "type": "Concept/Entity/Event", "weight": 0.8}
            ],
            "edges": [
                {"source": "EntityA", "target": "EntityB", "relation": "RELATION_TYPE", "weight": 0.9}
            ]
        }
        
        Rules:
        1. Nodes should be canonical (e.g., use "Python" not "python programming").
        2. Relations should be mostly: RELATED_TO, CAUSED_BY, HAS_A, IS_A, LIKES, DISLIKES.
        3. Weight represents confidence or importance (0.0 to 1.0).
        4. Focus on long-term value info, ignore chit-chat.
        """
        
        user_prompt = f"""
        Context: {context}
        Text: {content}
        
        Extract the Knowledge Graph:
        """
        
        # 这里其实应该调用 reasoner.think() 或者类似的接口
        # 假设 reasoner 有一个能够返回结构化数据的方法，或者我们需要解析它的思考结果
        # 为了简化，我们假设 reasoner.think 返回的是思考过程 + 最终答案
        # 我们这里模拟直接调用 LLM (实际项目中可能需要通过 Driver 或特定接口)
        
        # TODO: 由于 Reasoner 目前主要是 think-act 循环，这里我们可能需要
        # 1. 临时构造一个专门的 extraction chain
        # 2. 或者直接复用底层的 llm_client 如果有的话
        
        # 暂时使用 reasoner 的底层调用方式 (假设)
        # 实际代码中，Compressor 里是可以直接调 LLM 的。
        # 我们为了保持架构一致性，这里应该通过 Reasoner 的接口。
        # 但 Reasoner.think 是设计为 ReAct 循环的。
        # 作为一个 Service，我们可能更像 Compressor 那样直接调 LLM。
        
        # 修正：GraphExtractor 应该像 AutoClassifier 一样，拥有自己的 LLM Client 引用，或者由 Compressor 传入 client。
        # 这里我们假设它被注入了 llm_client
        raise NotImplementedError("LLM Client integration pending. Use Compressor's client in next step.")

