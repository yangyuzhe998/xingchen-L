"""
自动分类器 (Auto Classifier)
使用 LLM (S-Brain DeepSeek) 自动将对话/记忆归类到话题
"""
from typing import List, Dict, Optional, Tuple
from xingchen.utils.llm_client import LLMClient
from xingchen.utils.logger import logger
from xingchen.utils.json_parser import extract_json
from xingchen.memory.storage.topic_manager import topic_manager
from xingchen.config.prompts import MEMORY_CLASSIFY_PROMPT
from xingchen.utils.proxy import lazy_proxy


class AutoClassifier:
    """
    自动分类器
    使用 LLM 自动将对话归类到话题
    """
    
    def __init__(self, llm_provider: str = "deepseek"):
        """
        初始化分类器
        :param llm_provider: LLM 提供商 (默认使用 S脑 DeepSeek)
        """
        self.llm = LLMClient(provider=llm_provider)
        self.topic_manager = topic_manager
        logger.info(f"[AutoClassifier] Initialized with {llm_provider} LLM")
    
    def classify(self, content: str, auto_create: bool = True) -> Dict:
        """
        分类单条内容
        
        :param content: 待分类的内容
        :param auto_create: 是否自动创建新话题
        :return: 分类结果 {topic_id, task_id, is_new, confidence}
        """
        # 获取现有话题列表
        existing_topics = self._get_existing_topics_str()
        
        # 构建 Prompt
        prompt = MEMORY_CLASSIFY_PROMPT.format(
            existing_topics=existing_topics or "（暂无话题）",
            content=content[:2000]
        )
        
        # 调用 LLM
        logger.debug(f"[AutoClassifier] Calling LLM to classify: {content[:50]}...")
        try:
            response_obj = self.llm.chat([{"role": "user", "content": prompt}], temperature=0.3)
            response = response_obj.content if response_obj else None
            
            if not response:
                logger.warning("[AutoClassifier] LLM 未返回结果")
                return self._default_result()
            
            # 解析结果
            result = extract_json(response)
            if not result:
                logger.warning(f"[AutoClassifier] JSON 解析失败: {response[:100]}")
                return self._default_result()
            
            # 处理分类结果
            classification = self._process_classification(result, auto_create)
            return classification
            
        except Exception as e:
            logger.error(f"[AutoClassifier] 分类出错: {e}", exc_info=True)
            return self._default_result()

    def _get_existing_topics_str(self) -> str:
        """获取现有话题列表的字符串表示"""
        try:
            stats = self.topic_manager.get_stats()
            if stats["topics"] == 0:
                return ""
            
            # 获取所有话题
            topics = self.topic_manager.search_topics("", limit=50)
            
            if not topics:
                return ""
            
            lines = []
            for t in topics:
                name = t['metadata'].get("name", "未知")
                lines.append(f"- {name}")
            
            return "\n".join(lines)
        except Exception:
            return ""
    
    def _process_classification(self, result: Dict, auto_create: bool) -> Dict:
        """处理 LLM 的分类结果"""
        topic_name = result.get("topic_name", "默认话题")
        is_new_topic = result.get("is_new_topic", False)
        topic_description = result.get("topic_description", topic_name)
        task_name = result.get("task_name")
        task_description = result.get("task_description")
        confidence = result.get("confidence", 0.5)
        
        topic_id = None
        task_id = None
        
        if is_new_topic and auto_create:
            # 创建新话题
            topic_id = self.topic_manager.create_topic(topic_name, topic_description)
            logger.info(f"[AutoClassifier] 创建新话题: {topic_name}")
        else:
            # 查找现有话题
            existing = self.topic_manager.search_topics(topic_name, limit=1)
            if existing:
                topic_id = existing[0]["id"]
            elif auto_create:
                # 未找到但允许创建
                topic_id = self.topic_manager.create_topic(topic_name, topic_description)
        
        # 处理子任务
        if task_name and topic_id:
            task_id = self.topic_manager.create_task(topic_id, task_name, task_description)
        
        return {
            "topic_id": topic_id,
            "topic_name": topic_name,
            "task_id": task_id,
            "task_name": task_name,
            "is_new": is_new_topic,
            "confidence": confidence,
            "reason": result.get("reason", "")
        }
    
    def _default_result(self) -> Dict:
        """默认分类结果（分类失败时使用）"""
        return {
            "topic_id": None,
            "topic_name": "未分类",
            "task_id": None,
            "task_name": None,
            "is_new": False,
            "confidence": 0.0,
            "reason": "分类失败"
        }

    def classify_and_store(self, content: str, emotion_tag: str = "neutral",
                           category: str = "memory", meta: Dict = None) -> str:
        """分类并存储内容到对应话题"""
        classification = self.classify(content)
        
        fragment_id = self.topic_manager.add_fragment(
            content=content,
            topic_id=classification.get("topic_id"),
            task_id=classification.get("task_id"),
            emotion_tag=emotion_tag,
            category=category,
            meta={
                **(meta or {}),
                "classification_confidence": classification.get("confidence", 0),
                "auto_classified": True
            }
        )
        return fragment_id


_auto_classifier_instance: Optional[AutoClassifier] = None


def get_auto_classifier() -> AutoClassifier:
    """获取全局 AutoClassifier 实例（延迟初始化）。"""
    global _auto_classifier_instance
    if _auto_classifier_instance is None:
        _auto_classifier_instance = AutoClassifier(llm_provider="deepseek")
    return _auto_classifier_instance


auto_classifier = lazy_proxy(get_auto_classifier, AutoClassifier)
