import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.memory.storage.graph import GraphMemory

def test_graph_rag():
    print("Initializing GraphMemory...")
    # Use a temporary file for testing
    gm = GraphMemory("test_graph.json")
    
    print("\n1. Adding Triplets (Knowledge Injection)...")
    # User -> Likes -> Apple (Fruit)
    gm.add_triplet("User", "likes", "Apple", meta={"category": "food"})
    # Apple -> RichIn -> Vitamin C
    gm.add_triplet("Apple", "rich_in", "Vitamin C")
    # User -> Owns -> iPhone
    gm.add_triplet("User", "owns", "iPhone 15")
    # iPhone -> MadeBy -> Apple Inc
    gm.add_triplet("iPhone 15", "made_by", "Apple Inc")
    
    print("\n2. Searching Entity 'User'...")
    relations = gm.search_entity("User")
    for r in relations:
        print(f" - {r['source']} --[{r['relation']}]--> {r['target']}")
        
    print("\n3. Reasoning (Multi-hop)...")
    # Scenario: Why should User eat Apple?
    # Path: User -> Apple -> Vitamin C
    path = gm.get_path("User", "Vitamin C")
    print(f"Path from User to Vitamin C: {path}")
    
    # Scenario: What is the relationship between User and Apple Inc?
    # Path: User -> iPhone 15 -> Apple Inc
    path2 = gm.get_path("User", "Apple Inc")
    print(f"Path from User to Apple Inc: {path2}")

    # Clean up
    if os.path.exists("test_graph.json"):
        os.remove("test_graph.json")
        print("\nTest data cleaned up.")

if __name__ == "__main__":
    test_graph_rag()
