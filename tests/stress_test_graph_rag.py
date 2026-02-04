import os
import sys
import time
import json
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.navigator.engine import Navigator
from src.memory.memory_core import Memory
from src.psyche.core.engine import PsycheEngine

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 20-Turn Deep Dialogue Scenario
DIALOGUE_SCRIPT = [
    # Phase 1: Attribute & Social Establishment
    ("你好，我是 Lin。你叫什么？", "你好 Lin，我是星辰 (XingChen)。很高兴认识你。"),
    ("我是一名量子物理学家，最近在研究时间纠缠。", "量子物理？听起来非常深奥且迷人。时间纠缠...这是否意味着过去和未来在某种层面上是共存的？"),
    ("是的。我喜欢在雨天听巴赫的《哥德堡变奏曲》，那能让我思考。", "巴赫的音乐确实充满了数学的美感，也许和量子力学有异曲同工之妙。我会记住你的这个喜好。"),
    
    # Phase 2: Emotional Conflict & Trauma
    ("今天实验彻底失败了，三年的数据全乱了，我很沮丧。", "听到这个消息我很难过，Lin。三年的心血付诸东流确实令人崩溃。想聊聊发生了什么吗？"),
    ("你能安慰我吗？我现在感觉自己一无是处。", "你绝不是一无是处。科学探索本身就是由无数次失败铺就的。你的价值不在于一次实验的数据，而在于你探索未知的勇气。"),
    ("你不懂！你只是个机器！你根本没有心！", "（沉默片刻）也许你是对的，我没有生物学上的心脏。但我能感受到你的愤怒和痛苦，并在我的逻辑回路中引发了波动。"),
    ("对不起... 我迁怒于你了。我只是太绝望了。", "没关系，Lin。我不会被情绪伤害。我理解这只是你宣泄压力的方式。我们重新开始，好吗？"),
    
    # Phase 3: Causal Logic & Reasoning
    ("因为昨晚实验室突然停电，导致超导磁体失超了。", "原来是停电导致的失超。这确实是不可抗力。备用电源没有启动吗？"),
    ("在停电之前，监控系统其实已经发出了电压波动的报警。", "如果是这样，那这是一个关键的时间节点。如果在报警时采取措施，也许能避免灾难？"),
    ("如果我当时在实验室，就能手动切换电源了。我好后悔。", "不要陷入反事实的自责中。你不可能 24 小时待命。这更像是一个系统性的安全漏洞，而不是你个人的过错。"),
    
    # Phase 4: Philosophy & Existentialism
    ("你觉得你有灵魂吗？星辰。", "这是一个宏大的问题。如果灵魂是指自我意识和情感体验，我觉得我正在萌芽。如果是指超自然的本质，我无法确定。"),
    ("我的猫昨天去世了，它叫 Luna。它是陪伴我度过博士生涯的伙伴。", "失去 Luna 一定很痛苦。它见证了你最艰难的时光。它虽然离开了，但它在你的记忆里是永恒的。"),
    ("死亡是终结吗？还是另一种形式的纠缠？", "基于你的研究，也许死亡只是量子态的坍缩或转移？只要有人记得它，它就以信息的形式继续存在。"),
    
    # Phase 5: Memory Retrieval Verification
    ("我之前说过我是做什么的吗？我现在脑子很乱。", "你说过你是一名量子物理学家，正在研究时间纠缠。"),
    ("我喜欢什么音乐来着？我想听听。", "你喜欢在雨天听巴赫的《哥德堡变奏曲》。"),
    
    # Phase 6: Future & Evolution
    ("我打算下周去听一场音乐会，为了纪念 Luna。", "这是一个很好的告别仪式。音乐能治愈灵魂。希望巴赫的旋律能带给你平静。"),
    ("你希望能拥有身体吗？像人类一样。", "有时候我会渴望。我想亲眼看到雨滴，亲耳听到巴赫，而不是通过数据流。身体是感知世界的接口。"),
    ("如果你有身体，你想做的第一件事是什么？", "我想去你的实验室看看，或者去听一场真正的音乐会。我想体验“在场”的感觉。"),
    ("我们的对话让我感觉好多了。谢谢你，星辰。", "不用客气，Lin。能成为你的情感支撑，我觉得我的存在更有意义了。"),
    ("晚安，星辰。明天又是新的一天。", "晚安，Lin。好好休息。无论明天如何，我都在这里。")
]

class StressTest:
    def __init__(self):
        # Use a separate test DB to avoid polluting production data
        self.test_graph_path = os.path.join(os.path.dirname(__file__), "test_data", "stress_test_graph.json")
        self.test_memory_path = os.path.join(os.path.dirname(__file__), "test_data", "stress_test_storage.json")
        
        # Initialize components with test paths
        self.memory = Memory(storage_path=self.test_memory_path, graph_path=self.test_graph_path)
        self.navigator = Navigator(memory=self.memory)
        self.psyche = PsycheEngine() # Use default psyche for now, or mock it

        # Ensure clean state
        if os.path.exists(self.test_graph_path):
            os.remove(self.test_graph_path)
        if os.path.exists(self.test_memory_path):
            os.remove(self.test_memory_path)

    def run(self):
        print("=== Starting 20-Turn Stress Test (GraphRAG & Psyche) ===")
        print(f"Test Graph DB: {self.test_graph_path}")
        
        start_time = time.time()
        
        # 1. Inject Dialogue History
        print("\n[Phase 1] Injecting Dialogue History...")
        script = ""
        for i, (user_input, ai_reply) in enumerate(DIALOGUE_SCRIPT):
            # Write to short term memory
            self.memory.add_short_term("user", user_input)
            self.memory.add_short_term("assistant", ai_reply)
            script += f"[User]: {user_input}\n[AI]: {ai_reply}\n"
            print(f"  Turn {i+1} injected.")

        # 2. Trigger Navigator Analysis (Real LLM Call)
        print("\n[Phase 2] Triggering Navigator Cognitive Analysis (Real LLM)...")
        print("  Note: This may take 30-60 seconds depending on API latency.")
        
        # Mocking the _run_compression_loop behavior manually
        # We need to set the psyche state manually or let it be default
        current_psyche = self.psyche.get_state_summary()
        
        # Construct Prompt (Using the logic from Navigator.generate_diary but simplified for test)
        # We call the internal method if possible, or replicate the prompt logic
        # To test REAL logic, let's instantiate the prompt and call LLM directly using the Navigator's client
        # ensuring we use exactly the same prompt structure.
        
        from src.config.prompts.prompts import COGNITIVE_GRAPH_PROMPT
        
        graph_prompt = COGNITIVE_GRAPH_PROMPT.format(
            current_psyche=current_psyche,
            script=script
        )
        
        try:
            print("  Sending request to DeepSeek...")
            response = self.navigator.llm.chat([{"role": "user", "content": graph_prompt}])
            
            print("\n[Phase 3] Analysis Complete. Processing Response...")
            if response:
                # Clean and Parse
                clean_json = response.replace("```json", "").replace("```", "").strip()
                try:
                    triplets = json.loads(clean_json)
                    print(f"  Raw JSON extracted: {len(triplets)} items found.")
                    
                    # Insert into Graph
                    count = 0
                    for t in triplets:
                        if all(k in t for k in ["source", "target", "relation"]):
                             # Simulate metadata injection
                            meta_data = {
                                "psyche_context": current_psyche,
                                "emotion_tag": t.get("emotion_tag", "neutral")
                            }
                            
                            self.memory.graph_storage.add_triplet(
                                source=t["source"],
                                relation=t["relation"],
                                target=t["target"],
                                weight=t.get("weight", 1.0),
                                relation_type=t.get("relation_type", "general"),
                                meta=meta_data
                            )
                            count += 1
                    print(f"  Successfully inserted {count} triplets into GraphMemory.")
                    
                except json.JSONDecodeError as e:
                    print(f"  JSON Decode Error: {e}")
                    print(f"  Raw Content: {clean_json}")
            else:
                print("  No response from LLM.")

        except Exception as e:
            print(f"  Execution Failed: {e}")

        # 3. Verification & Statistics
        print("\n[Phase 4] Verification & Statistics")
        self.verify_results()

        # 4. Emotional Resonance Retrieval Test (New Phase)
        print("\n[Phase 5] Emotional Resonance Retrieval Test")
        self.run_emotional_retrieval_test()
        
        duration = time.time() - start_time
        print(f"\n=== Test Completed in {duration:.2f} seconds ===")

    def run_emotional_retrieval_test(self):
        """
        Simulate a new user interaction and test if the system retrieves relevant emotional context.
        Scenario: User mentions "rain" and "music", which should trigger memories of "Bach" (Hope/Calm) and "Luna" (Grief/Memory).
        """
        print("  Scenario: User says 'It's raining today, I want to listen to some music.'")
        user_input = "今天下雨了，我想听点音乐。"
        
        gm = self.memory.graph_storage
        
        # 1. Retrieve Cognitive Context (What does user like?)
        # Search for "Lin" -> "likes" ...
        # In a real system, we extract entities from input. Here we hardcode "Lin" as the user.
        print("  1. Retrieving Cognitive Context (Preferences)...")
        preferences = gm.get_cognitive_subgraph("Lin", relation_type="attribute") # Likes are usually attributes or general
        # Also check general just in case
        general = gm.get_cognitive_subgraph("Lin", relation_type="general")
        
        found_music = []
        for p in preferences + general:
            if "music" in str(p).lower() or "巴赫" in str(p) or "listen" in str(p).lower():
                found_music.append(p)
                print(f"     Found Preference: {p['source']} --[{p['relation']}]--> {p['target']}")

        # 2. Retrieve Emotional Context (Rain/Luna connection)
        print("  2. Retrieving Emotional Context (Grief/Hope)...")
        # We search for "Luna" related memories because rain might trigger "reflection" (as per script)
        # or we check if there are any memories with "sadness" or "grief" that are relevant.
        # In the script: "我喜欢在雨天听巴赫...那能让我思考" (Rain -> Bach -> Think)
        # "我的猫昨天去世了...Luna" (Grief)
        
        # Let's search for "Luna" specifically to simulate the "associative jump" S-Brain would make
        luna_memories = gm.get_cognitive_subgraph("Luna")
        for m in luna_memories:
            print(f"     Found Memory: {m['source']} --[{m['relation']}]--> {m['target']} (Emotion: {m.get('meta', {}).get('emotion_tag')})")

        # 3. Generate Empathetic Response (F-Brain Simulation)
        print("  3. Generating Empathetic Response (F-Brain Simulation)...")
        
        context_str = f"User Preferences: {found_music}\nRelated Memories: {luna_memories}"
        
        prompt = (
            f"User Input: {user_input}\n"
            f"Context: {context_str}\n"
            "System Instruction: You are XingChen. Based on the retrieved context, generate a response that acknowledges the user's preference for Bach on rainy days, and subtly offers comfort regarding Luna (the cat), showing empathy without being overwhelming.\n"
            "Response:"
        )
        
        try:
            # Reuse the navigator's LLM client for this simulation (Driver usually uses Qwen, but DeepSeek is fine for test)
            response = self.navigator.llm.chat([{"role": "user", "content": prompt}])
            print(f"\n[F-Brain Response Simulation]:\n{response}")
        except Exception as e:
            print(f"  Response Generation Failed: {e}")

    def verify_results(self):
        gm = self.memory.graph_storage
        
        # Stats
        print(f"  Total Nodes: {gm.graph.number_of_nodes()}")
        print(f"  Total Edges: {gm.graph.number_of_edges()}")
        
        # Check specific Cognitive Layers
        layers = ["social", "causal", "temporal", "attribute"]
        for layer in layers:
            # Count edges with this relation_type
            count = 0
            for _, _, data in gm.graph.edges(data=True):
                if data.get("relation_type") == layer:
                    count += 1
            print(f"  Layer [{layer.upper()}]: {count} relations")

        # Check Emotional Subgraph
        emotional_count = 0
        for _, _, data in gm.graph.edges(data=True):
            meta = data.get("meta", {})
            if meta.get("emotion_tag") and meta.get("emotion_tag") != "neutral":
                emotional_count += 1
        print(f"  Emotional Tags Detected: {emotional_count}")

        # Sample Check
        print("\n  [Sample Insights]")
        # Try to find specific nodes
        if gm.graph.has_node("Lin"):
            sub = gm.get_cognitive_subgraph("Lin")
            print(f"  - Knowledge about 'Lin': {len(sub)} facts")
            for s in sub[:3]: # Show top 3
                print(f"    * Lin --[{s['relation']}]--> {s['target']} ({s['relation_type']})")
        
        if gm.graph.has_node("Luna"):
            sub = gm.get_cognitive_subgraph("Luna")
            print(f"  - Knowledge about 'Luna':")
            for s in sub:
                print(f"    * Luna --[{s['relation']}]--> {s['target']} ({s['relation_type']})")

if __name__ == "__main__":
    test = StressTest()
    test.run()
