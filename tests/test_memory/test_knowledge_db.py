"""
测试 KnowledgeDB 模块
"""
import pytest
import os
import tempfile
from src.memory.storage.knowledge_db import KnowledgeDB


@pytest.fixture
def temp_knowledge_db(tmp_path):
    """创建临时测试数据库"""
    db = KnowledgeDB.__new__(KnowledgeDB)
    db.db_path = os.path.join(tmp_path, "test_knowledge.db")
    db._initialized = False
    db._init_database()
    db._initialized = True
    return db


class TestKnowledgeDBKnowledge:
    """测试 Knowledge CRUD"""
    
    def test_add_and_get_knowledge(self, temp_knowledge_db):
        db = temp_knowledge_db
        
        # 添加知识
        kid = db.add_knowledge(
            content="DeepSeek R1 于 2025年1月发布",
            category="fact",
            source="web_search"
        )
        
        assert kid > 0
        
        # 获取知识
        knowledge = db.get_knowledge(limit=10)
        assert len(knowledge) == 1
        assert knowledge[0]["content"] == "DeepSeek R1 于 2025年1月发布"
        assert knowledge[0]["category"] == "fact"
    
    def test_search_knowledge(self, temp_knowledge_db):
        db = temp_knowledge_db
        
        db.add_knowledge("Python 是一种编程语言", category="fact")
        db.add_knowledge("用户喜欢被叫仔仔", category="preference")
        
        # 搜索
        results = db.search_knowledge("Python")
        assert len(results) == 1
        assert "Python" in results[0]["content"]
    
    def test_update_confidence(self, temp_knowledge_db):
        db = temp_knowledge_db
        
        kid = db.add_knowledge("测试知识", confidence=0.5)
        db.update_knowledge_confidence(kid, 0.9)
        
        knowledge = db.get_knowledge()
        assert knowledge[0]["confidence"] == 0.9
    
    def test_delete_knowledge(self, temp_knowledge_db):
        db = temp_knowledge_db
        
        kid = db.add_knowledge("待删除的知识")
        assert len(db.get_knowledge()) == 1
        
        db.delete_knowledge(kid)
        assert len(db.get_knowledge()) == 0


class TestKnowledgeDBEntity:
    """测试 Entity CRUD"""
    
    def test_add_entity(self, temp_knowledge_db):
        db = temp_knowledge_db
        
        eid = db.add_entity(
            name="User",
            entity_type="person",
            aliases=["老杨", "仔仔"],
            description="系统的主人"
        )
        
        assert eid > 0
    
    def test_resolve_alias(self, temp_knowledge_db):
        db = temp_knowledge_db
        
        db.add_entity(
            name="User",
            entity_type="person",
            aliases=["老杨", "仔仔"]
        )
        
        # 测试别名解析
        assert db.resolve_alias("老杨") == "User"
        assert db.resolve_alias("仔仔") == "User"
        assert db.resolve_alias("User") == "User"
        assert db.resolve_alias("不存在") is None
    
    def test_add_alias_to_existing_entity(self, temp_knowledge_db):
        db = temp_knowledge_db
        
        db.add_entity(name="XingChen", aliases=["星辰"])
        db.add_entity_alias("XingChen", ["小星", "阿辰"])
        
        entity = db.get_entity_by_name("XingChen")
        assert "星辰" in entity["aliases"]
        assert "小星" in entity["aliases"]
        assert "阿辰" in entity["aliases"]
    
    def test_get_stats(self, temp_knowledge_db):
        db = temp_knowledge_db
        
        db.add_knowledge("知识1", category="fact")
        db.add_knowledge("知识2", category="fact")
        db.add_knowledge("偏好1", category="preference")
        db.add_entity("Entity1")
        
        stats = db.get_stats()
        assert stats["knowledge_count"] == 3
        assert stats["entity_count"] == 1
        assert stats["categories"]["fact"] == 2
        assert stats["categories"]["preference"] == 1
