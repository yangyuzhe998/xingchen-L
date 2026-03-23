import os
import re
import time
import json
from typing import Optional
from xingchen.utils.llm_client import LLMClient
from xingchen.config.prompts import EVOLUTION_SYSTEM_PROMPT
from .library import library_manager
from xingchen.tools.registry import tool_registry
from xingchen.utils.logger import logger
from xingchen.core.event_bus import event_bus
from xingchen.schemas.events import BaseEvent as Event


class EvolutionManager:
    """
    进化管理器 (Evolution Manager)
    负责处理 S脑 的进化请求。
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EvolutionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
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
        logger.info(f"[EvolutionManager] 🚀 Processing Evolution Request: {request}")
        
        # === Step 1: MCP First Strategy ===
        logger.info(f"[EvolutionManager] 🔍 Attempting to find existing MCP solution first...")
        if self._search_mcp_solution(request):
            logger.info(f"[EvolutionManager] ✅ MCP solution found and loaded. Skipping code generation.")
            msg = f"[System] 自我进化成功 (MCP Mode): 已加载外部 MCP 工具 ({request})。"
            self._notify_system(msg, memory)
            return

        logger.warning(f"[EvolutionManager] ⚠️ No suitable MCP found. Fallback to Code Generation.")
        
        # [Security Restriction] 用户要求暂时禁用代码生成能力
        logger.warning(f"[EvolutionManager] ⛔ Code Generation is currently DISABLED by user request.")
        msg = f"[System] 自我进化失败: 未找到合适的 MCP 工具，且代码生成能力已被暂时禁用。"
        self._notify_system(msg, memory)
        return

        # NOTE: 以下代码在 process_request 中不会执行，保留作为设计意图说明
        """
        # === Step 2: Code Generation Strategy ===
        # 1. Generate Code
        code = self._generate_skill_code(request)
        
        # 2. Extract Code/Structure
        if "Dockerfile" in code:
            self._deploy_docker_package(request, code)
        else:
            # 单文件模式
            ...
        """

    def _search_mcp_solution(self, request: str) -> bool:
        """搜索并尝试加载 MCP 解决方案"""
        try:
            # 1. 优先使用 Puppeteer MCP (如果已加载)
            if tool_registry.get_tool("puppeteer_navigate"):
                search_url = f"https://github.com/search?q={request.replace(' ', '+')}+mcp+server&type=repositories"
                tool_registry.execute("puppeteer_navigate", url=search_url)
                time.sleep(2)
                
                extract_script = """
                (() => {
                    const results = [];
                    const items = document.querySelectorAll('div[data-testid="results-list"] > div');
                    items.forEach(item => {
                        if (results.length >= 5) return;
                        const linkTag = item.querySelector('a');
                        const descTag = item.querySelector('span');
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
                        search_result = json.loads(eval_result)
                        if search_result:
                            formatted_results = []
                            for r in search_result:
                                formatted_results.append(f"Title: {r.get('title')}\nURL: {r.get('href')}\nDescription: {r.get('body')}\n")
                            
                            search_result_text = "\n---\n".join(formatted_results)
                            return self._analyze_search_results(request, search_result_text)
                    except json.JSONDecodeError:
                        pass
            
            # 2. 使用 WebSearch 查找 (Fallback)
            search_prompt = f"请将用户需求 '{request}' 转换为一个用于在 GitHub 上搜索 MCP Server 的英文关键词查询。只返回查询字符串，不要其他内容。"
            optimized_query = self._get_llm().chat([{"role": "user", "content": search_prompt}])
            if not optimized_query:
                optimized_query = f"{request} mcp server github"
            
            search_result = tool_registry.execute("web_search", query=optimized_query, max_results=5)
            if not search_result or "未找到" in str(search_result):
                return False
                
            return self._analyze_search_results(request, str(search_result))
            
        except Exception as e:
            logger.error(f"[EvolutionManager] MCP search failed: {e}")
            
        return False

    def _analyze_search_results(self, request, search_result_text):
        """分析搜索结果"""
        logger.info(f"[EvolutionManager] MCP search skipped (feature removed)")
        return False

    def _notify_system(self, msg, memory):
        event_bus.publish(Event(
            type="system_notification",
            source="evolution_manager",
            payload={"content": msg},
            meta={"level": "info"}
        ))
        
        if memory:
            try:
                memory.add_short_term(role="system", content=msg)
            except Exception as e:
                logger.error(f"[EvolutionManager] Failed to inject memory: {e}")
