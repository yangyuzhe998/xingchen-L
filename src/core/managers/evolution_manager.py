import os
import re
import time
import json
from typing import Optional
from ...utils.llm_client import LLMClient
from ...config.prompts.prompts import EVOLUTION_SYSTEM_PROMPT
from .library_manager import library_manager
from ...tools.registry import tool_registry

class EvolutionManager:
    """
    进化管理器 (Evolution Manager)
    负责处理 S脑 的进化请求，支持双重模式：
    1. MCP First: 优先搜索并加载现有的 MCP Server。
    2. Code Generation: 作为备选，生成 Python 代码并热加载。
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EvolutionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 延迟初始化 LLMClient 以避免循环依赖或过早初始化
        self.llm_client = None
        
    def _get_llm(self):
        if not self.llm_client:
            self.llm_client = LLMClient()
        return self.llm_client

    def process_request(self, request: str, memory=None):
        """
        处理进化请求
        :param request: e.g. "weather_tool - 获取天气信息"
        :param memory: Memory 实例，用于注入通知
        """
        print(f"[EvolutionManager] 🚀 Processing Evolution Request: {request}")
        
        # === Step 1: MCP First Strategy ===
        print(f"[EvolutionManager] 🔍 Attempting to find existing MCP solution first...")
        if self._search_mcp_solution(request):
            print(f"[EvolutionManager] ✅ MCP solution found and loaded. Skipping code generation.")
            # Notify System
            msg = f"[System] 自我进化成功 (MCP Mode): 已加载外部 MCP 工具 ({request})。"
            self._notify_system(msg, memory)
            return

        print(f"[EvolutionManager] ⚠️ No suitable MCP found. Fallback to Code Generation.")
        
        # [Security Restriction] 用户要求暂时禁用代码生成能力
        print(f"[EvolutionManager] ⛔ Code Generation is currently DISABLED by user request.")
        msg = f"[System] 自我进化失败: 未找到合适的 MCP 工具，且代码生成能力已被暂时禁用。"
        self._notify_system(msg, memory)
        return

        # === Step 2: Code Generation Strategy ===
        # 1. Generate Code
        # print(f"[EvolutionManager] Generating code for: {request}...")
        # code = self._generate_skill_code(request)
        # if not code:
        #     print("[EvolutionManager] ❌ Failed to generate code.")
        #     return

        # 2. Extract Code/Structure
        # 判断是单文件还是多文件(Docker Package)
        # 如果 LLM 输出包含文件结构描述（如 `__init__.py`, `Dockerfile`），我们需要解析并创建目录
        
        # 简单的启发式判断：如果包含 Dockerfile 字样，视为包模式
        if "Dockerfile" in code:
            print("[EvolutionManager] 📦 Detected Docker Package mode.")
            self._deploy_docker_package(request, code)
            filename = "package_mode" # 占位符
        else:
            # 单文件模式
            clean_code = self._extract_code(code)
            filename = self._extract_filename(clean_code)
            if not filename:
                safe_name = re.sub(r'[^a-zA-Z0-9]', '_', request.split('-')[0].strip())
                filename = f"{safe_name}_{int(time.time())}.py"
            
            filepath = os.path.join("src", "skills", filename)
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(clean_code)
                print(f"[EvolutionManager] ✅ Skill saved to {filepath}")
            except Exception as e:
                print(f"[EvolutionManager] ❌ Failed to write file: {e}")
                return

        # 5. Hot Reload
        print(f"[EvolutionManager] Reloading skills...")
        library_manager.scan_and_index()
        
        # 6. Notify System (Memory Injection)
        msg = f"[System] 自我进化成功 (Code Gen Mode): 已编写并加载技能 ({request})。"
        self._notify_system(msg, memory)

        print(f"[EvolutionManager] ✨ Evolution Complete.")

    def _search_mcp_solution(self, request: str) -> bool:
        """
        搜索并尝试加载 MCP 解决方案
        """
        try:
            # 1. 优先使用 Puppeteer MCP (如果已加载)
            if tool_registry.get_tool("puppeteer_navigate"):
                print(f"[EvolutionManager] 🔍 Using Puppeteer to search for MCP...")
                try:
                    # 构造 GitHub 搜索 URL
                    # 使用 GitHub 搜索，因为这是 MCP Server 最集中的地方
                    search_url = f"https://github.com/search?q={request.replace(' ', '+')}+mcp+server&type=repositories"
                    
                    # 1. 导航
                    print(f"[EvolutionManager] Puppeteer Navigating to: {search_url}")
                    tool_registry.execute("puppeteer_navigate", url=search_url)
                    
                    # 2. 等待加载 (简单的 sleep，或者依赖 navigate 的阻塞)
                    time.sleep(2)
                    
                    # 3. 提取结果 (使用 JS)
                    # 提取前 5 个仓库的标题和描述
                    extract_script = """
                    (() => {
                        const results = [];
                        // GitHub search results selectors (subject to change, using generic attributes where possible)
                        const items = document.querySelectorAll('div[data-testid="results-list"] > div');
                        
                        items.forEach(item => {
                            if (results.length >= 5) return;
                            const linkTag = item.querySelector('a');
                            const descTag = item.querySelector('span'); // Description usually in a span or p
                            
                            if (linkTag) {
                                results.push({
                                    title: linkTag.innerText,
                                    href: linkTag.href,
                                    body: descTag ? descTag.innerText : ''
                                });
                            }
                        });
                        return JSON.stringify(results);
                    })();
                    """
                    
                    eval_result = tool_registry.execute("puppeteer_evaluate", script=extract_script)
                    
                    if eval_result and isinstance(eval_result, str):
                        try:
                            # Puppeteer might return the stringified JSON directly or wrapped
                            # Clean up potential wrapper text if any (though tool usually returns raw result)
                            search_result = json.loads(eval_result)
                            print(f"[EvolutionManager] Puppeteer found {len(search_result)} results.")
                            
                            # 如果找到了结果，直接使用这些结果进行后续分析
                            if search_result:
                                # 格式化为类似 web_search 的输出供 LLM 分析
                                formatted_results = []
                                for r in search_result:
                                    formatted_results.append(f"Title: {r.get('title')}\nURL: {r.get('href')}\nDescription: {r.get('body')}\n")
                                
                                search_result_text = "\n---\n".join(formatted_results)
                                
                                # 跳过后续的 web_search
                                return self._analyze_search_results(request, search_result_text)
                                
                        except json.JSONDecodeError:
                            print("[EvolutionManager] Failed to parse Puppeteer JSON result.")
                            
                except Exception as e:
                    print(f"[EvolutionManager] ⚠️ Puppeteer search failed: {e}. Falling back to WebSearch.")
            
            # 2. 使用 WebSearch 查找 (Fallback)
            # 优化：同时使用中文和英文搜索，增加命中率
            # 尝试提取 request 中的英文关键词 (简单粗暴的分割)
            # 更好的做法是让 LLM 先翻译，这里简化处理，直接拼接通用关键词
            
            # 构造混合查询
            query = f"{request} mcp server github"
            
            # 再次尝试英文查询 (如果是中文请求)
            # 这里我们利用 LLM 先把 request 翻译成英文，这样搜索效果最好
            # 但为了节省一次 LLM 调用，我们直接搜混合词，或者信任 DuckDuckGo 的多语言能力
            
            # [Optimization]: 让 LLM 先优化搜索词
            search_prompt = f"请将用户需求 '{request}' 转换为一个用于在 GitHub 上搜索 MCP Server 的英文关键词查询。只返回查询字符串，不要其他内容。例如：'filesystem mcp server github'"
            optimized_query = self._get_llm().chat([{"role": "user", "content": search_prompt}])
            if not optimized_query:
                optimized_query = query # Fallback
            
            print(f"[EvolutionManager] 🔍 Searching with query: {optimized_query}")
            search_result = tool_registry.execute("web_search", query=optimized_query, max_results=5)
            
            if not search_result or "未找到" in str(search_result):
                return False
                
            # 2. 让 LLM 分析搜索结果，提取 Config
            return self._analyze_search_results(request, str(search_result))
            
        except Exception as e:
            print(f"[EvolutionManager] MCP search failed: {e}")
            
        return False

    def _analyze_search_results(self, request, search_result_text):
        """
        分析搜索结果并尝试提取 MCP Config
        """
        prompt = f"""
请分析以下关于 MCP Server 的搜索结果，判断是否有能够满足需求 "{request}" 的现成 MCP Server。
如果存在，请提取其运行命令（通常是 `npx` 或 `docker run`）。

搜索结果：
{search_result_text}

请返回如下 JSON 格式（不要Markdown）：
{{
    "found": true/false,
    "config": {{
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-xxx"]
    }}
}}
如果没找到或不确定，found 为 false。
"""
        llm_response = self._get_llm().chat([{"role": "user", "content": prompt}])
        
        try:
            clean_json = llm_response.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean_json)
            
            if result.get("found") and result.get("config"):
                config = result["config"]
                print(f"[EvolutionManager] 🎯 Found potential MCP: {config}")
                return library_manager.load_mcp_tool(config)
                
        except json.JSONDecodeError:
            print(f"[EvolutionManager] Failed to parse LLM response for MCP search.")
            
        return False

    def _notify_system(self, msg, memory):
        from src.core.bus import event_bus, Event
        event_bus.publish(Event(
            type="system_notification",
            source="evolution_manager",
            payload={"content": msg},
            meta={"level": "info"}
        ))
        
        if memory:
            try:
                # 修复: add_short_term 参数顺序 (role, content)
                memory.add_short_term(role="system", content=msg)
                print(f"[EvolutionManager] Memory injected.")
            except Exception as e:
                print(f"[EvolutionManager] Failed to inject memory: {e}")

    def _deploy_docker_package(self, request, llm_response):
        """
        解析 LLM 返回的多文件结构并部署到 src/skills/<skill_name>
        假设 LLM 返回格式类似：
        ### src/skills/my_skill/Dockerfile
        ```dockerfile
        ...
        ```
        """
        # 1. 确定包名
        # 尝试从 Dockerfile 路径或 request 中提取
        # 优化: 去除可能的序号前缀 (e.g. "2. audio_extractor" -> "audio_extractor")
        raw_name = request.split('-')[0].strip()
        clean_name = re.sub(r'^[\d\.\s]+', '', raw_name)
        skill_name = re.sub(r'[^a-zA-Z0-9]', '_', clean_name).lower()
        
        package_dir = os.path.join("src", "skills", skill_name)
        
        if not os.path.exists(package_dir):
            os.makedirs(package_dir)
            
        # 2. 解析文件块
        # 正则匹配：文件名 + 代码块
        # 格式支持: 
        # File: filename
        # ```ext
        # content
        # ```
        
        # 这是一个简化的解析器
        files = {}
        current_file = None
        current_content = []
        in_code_block = False
        
        lines = llm_response.split('\n')
        for line in lines:
            # 识别文件名行 (兼容多种 LLM 输出格式)
            # e.g. "1. `Dockerfile`", "File: app.py", "### Dockerfile", "**manifest.json**"
            file_match = re.search(r'[`\s#\*]([\w\.]+)\s*(\(.*\))?$', line) 
            
            # 如果当前行看起来像文件名，且不是代码块的一部分
            if not in_code_block:
                # 特殊处理：有些 LLM 会直接输出文件名，没有反引号
                clean_line = line.strip().replace('*', '').replace('#', '').strip()
                if clean_line in ['Dockerfile', 'manifest.json', 'app.py', '__init__.py'] or \
                   (clean_line.endswith('.py') or clean_line.endswith('.json')):
                    
                    # 如果之前有未保存的文件内容，先保存
                    if current_file and current_content:
                        files[current_file] = "\n".join(current_content)
                    
                    current_file = clean_line
                    current_content = []
                    continue
            
            if line.strip().startswith('```'):
                if in_code_block:
                    # End block
                    in_code_block = False
                    if current_file:
                        files[current_file] = "\n".join(current_content)
                        # current_file = None # 不清空，防止 LLM 在代码块后还有注释
                else:
                    # Start block
                    in_code_block = True
                continue
                
            if in_code_block and current_file:
                current_content.append(line)

        # 处理最后一个文件
        if current_file and current_content:
            files[current_file] = "\n".join(current_content)

        # 3. 写入文件
        for fname, content in files.items():
            fpath = os.path.join(package_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[EvolutionManager] 📦 Wrote {fname}")
            
        # 确保有 __init__.py
        init_path = os.path.join(package_dir, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write("")

    def _generate_skill_code(self, request: str) -> str:
        """
        调用 LLM 生成符合规范的技能代码
        """
        # 读取开发规范
        standard_path = os.path.join("docs", "dev", "skill_standard.md")
        try:
            with open(standard_path, "r", encoding="utf-8") as f:
                standard = f.read()
        except Exception:
            standard = "Standard not found. Please ensure code follows Python best practices."

        prompt = EVOLUTION_SYSTEM_PROMPT.format(
            request=request,
            standard=standard
        )
        messages = [{"role": "user", "content": prompt}]
        return self._get_llm().chat(messages)

    def _extract_code(self, text: str) -> str:
        """从 LLM 回复中提取代码块"""
        match = re.search(r"```python(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # 尝试匹配没有 python 标签的代码块
        match = re.search(r"```(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
            
        return text.strip()

    def _extract_filename(self, code: str) -> Optional[str]:
        """尝试从代码中提取工具名作为文件名"""
        # 查找 @tool_registry.register(name="tool_name", ...)
        match = re.search(r'name=["\'](.*?)["\']', code)
        if match:
            return f"{match.group(1)}.py"
        return None

# 全局实例
evolution_manager = EvolutionManager()
