"""
测试 TopicManager 模块
"""
import pytest
import os
import shutil
import tempfile
from xingchen.memory.storage.topic_manager import TopicManager


@pytest.fixture
def temp_topic_manager(tmp_path):
    """创建临时测试实例"""
    # 创建新实例 (绕过单例)
    manager = TopicManager.__new__(TopicManager)
    manager._initialized = False
    
    # 设置临时路径
    import chromadb
    db_path = os.path.join(tmp_path, "test_topic_db")
    os.makedirs(db_path, exist_ok=True)
    
    manager.client = chromadb.PersistentClient(path=db_path)
    manager.topics = manager.client.get_or_create_collection(name="topics")
    manager.tasks = manager.client.get_or_create_collection(name="tasks")
    manager.fragments = manager.client.get_or_create_collection(name="fragments")
    manager._initialized = True
    
    return manager


class TestTopicOperations:
    """测试话题操作"""
    
    def test_create_topic(self, temp_topic_manager):
        manager = temp_topic_manager
        
        topic_id = manager.create_topic("项目讨论", "关于星辰项目的讨论")
        
        assert topic_id.startswith("topic_")
        assert manager.topics.count() == 1
    
    def test_get_topic(self, temp_topic_manager):
        manager = temp_topic_manager
        
        topic_id = manager.create_topic("学习Python", "Python 学习笔记")
        topic = manager.get_topic(topic_id)
        
        assert topic is not None
        assert topic["metadata"]["name"] == "学习Python"
    
    def test_search_topics(self, temp_topic_manager):
        manager = temp_topic_manager
        
        manager.create_topic("机器学习", "AI 和 ML 相关")
        manager.create_topic("烹饪食谱", "美食制作")
        
        results = manager.search_topics("人工智能")
        assert len(results) > 0
        # 机器学习应该排在前面
        assert "机器学习" in results[0]["document"] or "机器学习" in results[0]["metadata"].get("name", "")


class TestTaskOperations:
    """测试任务操作"""
    
    def test_create_task(self, temp_topic_manager):
        manager = temp_topic_manager
        
        topic_id = manager.create_topic("项目开发")
        task_id = manager.create_task(topic_id, "需求评审", "评审产品需求文档")
        
        assert task_id.startswith("task_")
        assert manager.tasks.count() == 1


class TestFragmentOperations:
    """测试片段操作"""
    
    def test_add_fragment(self, temp_topic_manager):
        manager = temp_topic_manager
        
        frag_id = manager.add_fragment(
            content="用户说喜欢被叫仔仔",
            emotion_tag="happy",
            category="preference"
        )
        
        assert frag_id.startswith("frag_")
