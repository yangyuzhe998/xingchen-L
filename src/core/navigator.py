from utils.llm_client import LLMClient
from psyche.psyche_core import PsycheState
from memory.memory_core import Memory

class Navigator:
    """
    S脑 (Slow Brain) / 慢脑
    负责：长期规划、深度分析、反思总结。
    特点：异步运行，不直接控制输出，通过 Suggestion Board 给 Driver 提建议。
    模型：DeepSeek
    """
    def __init__(self, name="Navigator", memory=None):
        self.name = name
        # S脑使用 DeepSeek
        self.llm = LLMClient(provider="deepseek")
        self.memory = memory if memory else Memory()
        self.suggestion_board = []
        print(f"[{self.name}] 初始化完成。模型: DeepSeek。")

    def analyze(self, current_input):
        """
        分析当前上下文，生成：
        1. 长期规划或建议 (Suggestion)
        2. 心智状态评分 (Psyche Update)
        3. 长期记忆沉淀 (LongTerm Memory)
        """
        print(f"[{self.name}] 正在深度分析上下文...")
        
        # 获取历史记录和长期记忆
        history = self.memory.get_recent_history(limit=10)
        long_term_context = self.memory.get_relevant_long_term()
        
        # 将历史记录转换为字符串
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
        
        system_prompt = f"""你是一个高智商的AI“领航员”(S脑)。
你的任务是观察“驾驶员”(F脑)与用户的对话，并进行深度分析。
{long_term_context}

你需要输出三部分内容：
1. **建议 (Suggestion)**: 给驾驶员的简短建议，关于接下来的对话策略或注意事项。
2. **心智评分 (Psyche Score)**: 根据对话内容，评估心智状态的**变化量 (Delta)**。
3. **记忆 (Memory)**: (可选) 如果对话中包含了值得记住的重要事实或用户偏好，请提取出来。

心智状态包含四个维度 (-0.1 到 +0.1 之间):
- curiosity (好奇): 是否发现了新奇信息？
- interest (利益): 是否符合自身利益/生存目标？
- morality (道德): 是否符合价值观？
- fear (恐惧): 是否有风险或压力？

请以如下格式返回（不要包含Markdown代码块）：
Suggestion: [你的建议]
Delta: [curiosity, interest, morality, fear] (例如: [0.05, 0.0, -0.01, 0.0])
Memory: [需要记住的内容] (如果没有则不输出此行)
"""
        
        user_prompt = f"""
对话历史:
{history_text}
User Input: {current_input}

请开始分析。
"""

        try:
            response = self.llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # 简单解析返回结果
            suggestion = "继续保持。"
            delta = PsycheState(0, 0, 0, 0)
            
            lines = response.split('\n')
            for line in lines:
                if line.startswith("Suggestion:"):
                    suggestion = line.replace("Suggestion:", "").strip()
                elif line.startswith("Delta:"):
                    try:
                        # 解析列表字符串 [0.1, 0.0, ...]
                        vals_str = line.replace("Delta:", "").strip().strip("[]")
                        vals = [float(x.strip()) for x in vals_str.split(',')]
                        if len(vals) == 4:
                            delta = PsycheState(vals[0], vals[1], vals[2], vals[3])
                    except Exception as e:
                        print(f"[{self.name}] 解析 Delta 失败: {e}")
                elif line.startswith("Memory:"):
                    memory_content = line.replace("Memory:", "").strip()
                    if memory_content and memory_content.lower() != "none":
                        self.memory.add_long_term(memory_content, category="fact")

            self.suggestion_board.append(suggestion)
            print(f"[{self.name}] 分析结果 -> 建议: {suggestion} | 心智变化: {delta}")
            
            return suggestion, delta

        except Exception as e:
            print(f"[{self.name}] 分析出错: {e}")
            return None, None


    def get_suggestions(self):
        return self.suggestion_board
