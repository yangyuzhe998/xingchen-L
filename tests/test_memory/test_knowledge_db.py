"""
测试 KnowledgeDB 模块
"""
import pytest
import os
import tempfile
from xingchen.memory.storage.knowledge_db import KnowledgeDB


@pytest.fixture
def temp_knowledge_db(tmp_path):
    """创建临时测试数据库"""
    db = KnowledgeDB.__new__(KnowledgeDB)
    db.db_path = os.path.join(tmp_path, "test_knowledge.db")
    db._initialized = False
    db._init_db()
    db._initialized = True
    return db


class TestKnowledgeDBKnowledge:
    """测试 Knowledge CRUD"""
    
    def test_add_and_get_knowledge(self, temp_knowledge_db):
        db = temp_knowledge_db
        
        # 添加知识
        kid = db.add_knowledge(
            content="DeepSeek R1 于 2025年 1月发布",
            category="fact",
            source="web_search"
        )
        
        assert kid > 0
        
        # 获取知识
        knowledge = db.get_knowledge(limit=10)
        assert len(knowledge) == 1
        assert knowledge[0]["content"] == "DeepSeek R1 于 2025年 1月发布"
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
            description="系统的主要用户"
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
