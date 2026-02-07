"""
测试 TopicManager 模块
"""
import pytest
import os
import shutil
import tempfile
from src.memory.storage.topic_manager import TopicManager


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
    
    def test_get_tasks_by_topic(self, temp_topic_manager):
        manager = temp_topic_manager
        
        topic_id = manager.create_topic("测试话题")
        manager.create_task(topic_id, "任务1")
        manager.create_task(topic_id, "任务2")
        manager.create_task(topic_id, "任务3")
        
        tasks = manager.get_tasks_by_topic(topic_id)
        assert len(tasks) == 3


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
        assert manager.fragments.count() == 1
    
    def test_add_fragment_with_hierarchy(self, temp_topic_manager):
        manager = temp_topic_manager
        
        topic_id = manager.create_topic("用户偏好")
        task_id = manager.create_task(topic_id, "称呼习惯")
        
        frag_id = manager.add_fragment(
            content="用户喜欢被叫仔仔",
            topic_id=topic_id,
            task_id=task_id,
            category="preference"
        )
        
        # 验证层级查询
        results = manager.get_fragments_by_topic(topic_id)
        assert len(results) == 1
        assert results[0]["metadata"]["task_id"] == task_id
    
    def test_search_fragments(self, temp_topic_manager):
        manager = temp_topic_manager
        
        manager.add_fragment("Python 是一种编程语言", category="knowledge")
        manager.add_fragment("用户喜欢深色主题", category="preference")
        
        results = manager.search_fragments("编程语言")
        assert len(results) > 0
        # 检查是否能搜到相关内容 (语义搜索可能返回多个结果)
        found_python = any("Python" in r["document"] for r in results)
        assert found_python, f"Expected to find Python in results: {results}"
    
    def test_search_fragments_with_filter(self, temp_topic_manager):
        manager = temp_topic_manager
        
        topic_id = manager.create_topic("技术学习")
        
        manager.add_fragment("Python 基础语法", topic_id=topic_id, category="knowledge")
        manager.add_fragment("Java 面向对象", topic_id=topic_id, category="knowledge")
        manager.add_fragment("用户偏好设置", category="preference")  # 不属于该话题
        
        # 按话题过滤
        results = manager.search_fragments("语法", topic_id=topic_id)
        assert len(results) >= 1
        assert all(r["metadata"].get("topic_id") == topic_id for r in results)


class TestStatistics:
    """测试统计功能"""
    
    def test_get_stats(self, temp_topic_manager):
        manager = temp_topic_manager
        
        topic_id = manager.create_topic("测试话题")
        manager.create_task(topic_id, "测试任务")
        manager.add_fragment("测试片段1")
        manager.add_fragment("测试片段2")
        
        stats = manager.get_stats()
        assert stats["topics"] == 1
        assert stats["tasks"] == 1
        assert stats["fragments"] == 2
