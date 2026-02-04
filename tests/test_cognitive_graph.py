import os
import sys
import json
import unittest
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.memory.storage.graph import GraphMemory

class TestCognitiveGraph(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "tests/test_cognitive_graph.json"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.gm = GraphMemory(self.test_db_path)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_cognitive_extraction_simulation(self):
        print("\n=== Testing Cognitive Graph Extraction Simulation ===")
        
        # Simulated LLM output
        llm_output_json = [
            {"source": "User", "relation": "dislikes", "target": "Broccoli", "relation_type": "social", "weight": 0.9},
            {"source": "Rain", "relation": "causes", "target": "Wet Ground", "relation_type": "causal", "weight": 1.0},
            {"source": "Breakfast", "relation": "happens_before", "target": "Lunch", "relation_type": "temporal", "weight": 1.0},
            {"source": "Apple", "relation": "is", "target": "Red", "relation_type": "attribute", "weight": 0.8}
        ]
        
        # Simulate insertion loop
        count = 0
        for t in llm_output_json:
            self.gm.add_triplet(
                source=t["source"],
                relation=t["relation"],
                target=t["target"],
                weight=t.get("weight", 1.0),
                relation_type=t.get("relation_type", "general")
            )
            count += 1
        
        print(f"Inserted {count} triplets.")
        
        # Verify specific cognitive subgraphs
        
        # 1. Social Layer
        social_graph = self.gm.get_cognitive_subgraph("User", relation_type="social")
        print(f"Social Subgraph for User: {social_graph}")
        self.assertEqual(len(social_graph), 1)
        self.assertEqual(social_graph[0]["target"], "Broccoli")
        self.assertEqual(social_graph[0]["relation_type"], "social")
        
        # 2. Causal Layer
        causal_graph = self.gm.get_cognitive_subgraph("Rain", relation_type="causal")
        print(f"Causal Subgraph for Rain: {causal_graph}")
        self.assertEqual(len(causal_graph), 1)
        self.assertEqual(causal_graph[0]["target"], "Wet Ground")
        
        # 3. Temporal Layer
        temporal_graph = self.gm.get_cognitive_subgraph("Breakfast", relation_type="temporal")
        print(f"Temporal Subgraph for Breakfast: {temporal_graph}")
        self.assertEqual(len(temporal_graph), 1)
        
        # 4. Attribute Layer
        attr_graph = self.gm.get_cognitive_subgraph("Apple", relation_type="attribute")
        print(f"Attribute Subgraph for Apple: {attr_graph}")
        self.assertEqual(len(attr_graph), 1)

    def test_weight_update(self):
        print("\n=== Testing Weight Update ===")
        
        # Initial insert
        self.gm.add_triplet("User", "likes", "Coding", weight=0.5, relation_type="social")
        
        # Update with higher weight
        self.gm.add_triplet("User", "likes", "Coding", weight=0.9, relation_type="social")
        
        # Verify
        subgraph = self.gm.get_cognitive_subgraph("User", relation_type="social")
        self.assertEqual(len(subgraph), 1)
        self.assertEqual(subgraph[0]["weight"], 0.9)
        print(f"Updated weight: {subgraph[0]['weight']}")

    def test_emotional_context(self):
        print("\n=== Testing Emotional Context Integration ===")
        
        # Simulate Psyche context injection
        current_psyche = "Happy and curious"
        
        # Add triplet with emotion_tag and psyche_context
        self.gm.add_triplet(
            source="User",
            relation="gave_gift",
            target="AI",
            relation_type="social",
            meta={
                "emotion_tag": "happy",
                "psyche_context": current_psyche
            }
        )
        
        # Add neutral triplet
        self.gm.add_triplet(
            source="User",
            relation="asked",
            target="Weather",
            relation_type="general",
            meta={
                "emotion_tag": "neutral"
            }
        )
        
        # Verify Emotional Subgraph Retrieval
        happy_memories = self.gm.get_emotional_subgraph("User", emotion_tag="happy")
        print(f"Happy Memories: {happy_memories}")
        
        self.assertEqual(len(happy_memories), 1)
        self.assertEqual(happy_memories[0]["relation"], "gave_gift")
        self.assertEqual(happy_memories[0]["psyche_context"], current_psyche)
        
        # Verify Filtering
        neutral_memories = self.gm.get_emotional_subgraph("User", emotion_tag="neutral")
        self.assertEqual(len(neutral_memories), 1)
        self.assertEqual(neutral_memories[0]["relation"], "asked")

if __name__ == "__main__":
    unittest.main()
