from utils.llm_client import LLMClient
from psyche.psyche_core import PsycheState
from memory.memory_core import Memory
from core.bus import event_bus
from config.prompts import NAVIGATOR_SYSTEM_PROMPT, NAVIGATOR_USER_PROMPT
from config.settings import settings
import json
import os

class Navigator:
    """
    S脑 (Slow Brain) / 慢脑
    负责：长期规划、深度分析、反思总结。
    特点：异步运行，不直接控制输出，通过 Suggestion Board 给 Driver 提建议。
    模型：DeepSeek (模拟 R1 推理模式)
    """
    def __init__(self, name="Navigator", memory=None):
        self.name = name
        # S脑使用 DeepSeek
        self.llm = LLMClient(provider="deepseek")
        # 强制切换为 deepseek-reasoner
        self.llm.model = "deepseek-reasoner"
        self.memory = memory if memory else Memory()
        self.suggestion_board = []
        print(f"[{self.name}] 初始化完成。模型: DeepSeek (R1)。")

    def _build_static_context(self):
        """
        构建静态上下文 (Static Context)
        利用 DeepSeek 的 Prefix Caching 机制，这部分内容应该保持不变。
        
        【动态扫描机制】
        这里不再写死文件列表，而是动态扫描 src 目录下所有的 Python 代码文件。
        这样当项目结构调整或文件增加时，S脑能自动感知到最新的代码架构。
        注意：我们会对文件路径进行排序，确保生成的 Prompt 前缀一致，从而命中 Cache。
        """
        project_context = ""
        project_root = settings.PROJECT_ROOT
        src_path = os.path.join(project_root, "src")
        
        try:
            # 动态收集所有 .py 文件
            code_files = []
            for root, dirs, files in os.walk(src_path):
                # 排除 __pycache__ 等目录
                if "__pycache__" in dirs:
                    dirs.remove("__pycache__")
                
                for file in files:
                    if file.endswith(".py"):
                        full_path = os.path.join(root, file)
                        # 计算相对路径，用于显示 (例如 src/core/driver.py)
                        rel_path = os.path.relpath(full_path, project_root).replace("\\", "/")
                        code_files.append((rel_path, full_path))
            
            # 关键：必须排序！否则文件顺序随机变化会导致 Cache 失效 (Prefix Hash 改变)
            code_files.sort(key=lambda x: x[0])
            
            loaded_count = 0
            MAX_FILE_SIZE = settings.MAX_CODE_SCAN_SIZE
            
            for rel_path, full_path in code_files:
                try:
                    # 检查文件大小
                    file_size = os.path.getsize(full_path)
                    if file_size > MAX_FILE_SIZE:
                        print(f"[{self.name}] 跳过大文件 {rel_path} ({file_size/1024:.1f}KB)")
                        continue
                        
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        project_context += f"\n=== File: {rel_path} ===\n{content}\n"
                        loaded_count += 1
                except Exception as read_err:
                    print(f"[{self.name}] 读取文件失败 {rel_path}: {read_err}")
            
            # print(f"[{self.name}] 已加载静态上下文: {loaded_count} 个文件")
            
        except Exception as e:
            print(f"[{self.name}] 静态上下文构建失败: {e}")

        static_prompt = NAVIGATOR_SYSTEM_PROMPT.format(project_context=project_context)
        return static_prompt

    def analyze_cycle(self):
        """
        基于 EventBus 的周期性分析 (R1 模式)
        """
        print(f"[{self.name}] 正在进行周期性深度推理 (R1 Mode)...")
        
        events = event_bus.get_latest_cycle(limit=50)
        if not events:
            return None, None

        script = ""
        for e in events:
            timestamp_str = f"{e.timestamp:.2f}"
            if e.type == "user_input":
                script += f"[{timestamp_str}] User: {e.payload.get('content')}\n"
            elif e.type == "driver_response":
                meta = e.meta
                inner_voice = meta.get('inner_voice', 'N/A')
                emotion = meta.get('user_emotion_detect', 'N/A')
                script += f"[{timestamp_str}] Driver (Inner: {inner_voice}) [Detect: {emotion}]: {e.payload.get('content')}\n"

        # 动态部分：长期记忆 + 最近日志
        # 注意：为了命中 Cache，system_prompt (static) 必须放在最前面且完全不变
        # 动态内容只能追加在后面 (user message)
        
        long_term_context = self.memory.get_relevant_long_term()
        
        static_system_prompt = self._build_static_context()
        
        dynamic_user_prompt = NAVIGATOR_USER_PROMPT.format(
            long_term_context=long_term_context,
            script=script
        )

        try:
            # 模拟 R1 的长思考过程
            # print(f"[{self.name}] Thinking...") 
            response = self.llm.chat([
                {"role": "system", "content": static_system_prompt},
                {"role": "user", "content": dynamic_user_prompt}
            ])
            
            print(f"[{self.name}] R1 原始回复:\n{response}")

            # 解析结果
            suggestion = "维持当前策略。"
            delta = None
            
            lines = response.split('\n')
            for line in lines:
                clean_line = line.strip().replace('*', '') # 去除 markdown 加粗
                if clean_line.startswith("Suggestion:") or clean_line.startswith("Suggestion："):
                    suggestion = clean_line.replace("Suggestion:", "").replace("Suggestion：", "").strip()
                elif clean_line.startswith("Delta:"):
                    try:
                        vals_str = clean_line.replace("Delta:", "").strip().strip("[]")
                        vals = [float(x.strip()) for x in vals_str.split(',')]
                        if len(vals) == 4:
                            delta = PsycheState(vals[0], vals[1], vals[2], vals[3])
                    except: pass
                elif clean_line.startswith("Memory:"):
                    memory_content = clean_line.replace("Memory:", "").strip()
                    if memory_content and memory_content.lower() != "none":
                        self.memory.add_long_term(memory_content, category="fact")

            self.suggestion_board.append(suggestion)
            print(f"[{self.name}] 周期分析完成 -> 建议: {suggestion}")
            
            return suggestion, delta

        except Exception as e:
            print(f"[{self.name}] 分析出错: {e}")
            return None, None

    # 保留旧接口以兼容（或者直接废弃）
    def analyze(self, current_input):
        return self.analyze_cycle()
