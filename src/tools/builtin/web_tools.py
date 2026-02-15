

import asyncio
from src.tools.registry import ToolRegistry, ToolTier
from src.utils.logger import logger

# Check for crawl4ai
try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    logger.warning("[WebTools] crawl4ai not installed. 'web_crawl' tool will be disabled.")

# Check for duckduckgo_search
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    logger.warning("[WebTools] duckduckgo-search not installed. 'web_search' tool will be disabled.")

@ToolRegistry.register(
    name="web_search",
    description="[国内可用/本地版] 使用 DuckDuckGo 进行网络搜索。支持获取搜索结果的标题、链接和摘要。",
    tier=ToolTier.SLOW,
    schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "max_results": {"type": "integer", "description": "最大结果数量 (默认 5)", "default": 5}
        },
        "required": ["query"]
    }
)
def web_search(query: str, max_results: int = 5):
    """
    使用 DuckDuckGo 搜索
    """
    if not DDGS_AVAILABLE:
        return "Error: 缺少依赖 'duckduckgo-search'。请运行 `pip install duckduckgo-search`。"
    
    try:
        logger.info(f"[WebTools] Searching for: {query} (Max: {max_results})")
        results = DDGS().text(query, max_results=max_results)
        if not results:
            logger.info(f"[WebTools] No results found for: {query}")
            return "No results found."
            
        formatted_results = ""
        for i, r in enumerate(results):
            formatted_results += f"{i+1}. [{r['title']}]({r['href']})\n   {r['body']}\n\n"
        
        logger.info(f"[WebTools] Search completed. Found {len(results)} results.")
        return formatted_results
    except Exception as e:
        logger.error(f"[WebTools] Search failed: {e}", exc_info=True)
        return f"Search Error: {str(e)}"

import os
import hashlib
from datetime import datetime
from src.config.settings.settings import settings


def _run_coro_sync(coro, timeout: float = 60.0):
    """在同步函数中安全运行 coroutine。

    - 若当前线程没有运行中的 event loop：使用 asyncio.run
    - 若已有运行中的 event loop（典型：Web/Uvicorn 环境）：在新线程中启动独立 loop 执行

    返回 coroutine 的结果；异常会向外抛出。
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import threading

    result_container = {"result": None, "error": None}

    def runner():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result_container["result"] = loop.run_until_complete(coro)
        except Exception as e:
            result_container["error"] = e
        finally:
            try:
                loop.close()
            except Exception:
                pass

    t = threading.Thread(target=runner, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        raise TimeoutError(f"Coroutine did not finish within {timeout}s")
    if result_container["error"] is not None:
        raise result_container["error"]

    return result_container["result"]


@ToolRegistry.register(
    name="web_crawl",
    description="[国内可用/本地版] 使用 Crawl4AI (Playwright) 抓取网页内容。自动保存到知识库临时区。适合读取长文章。",
    tier=ToolTier.SLOW,
    schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "要抓取的网页 URL"},
            "bypass_cache": {"type": "boolean", "description": "是否强制刷新缓存 (默认 False)", "default": False}
        },
        "required": ["url"]
    }
)
def web_crawl(url: str, bypass_cache: bool = False):
    """
    同步包装器，调用异步爬虫，并将结果保存到文件
    """
    if not CRAWL4AI_AVAILABLE:
        return "Error: 缺少依赖 'crawl4ai'。请运行 `pip install crawl4ai` 和 `playwright install`。"

    # [Fix] URL 清洗逻辑
    # 移除可能的 Markdown 链接格式 (e.g. [title](url))
    url = url.strip()
    if url.startswith("[") and "](" in url and url.endswith(")"):
        # 提取括号内的 URL
        try:
            url = url.split("](")[1][:-1]
        except:
            pass
            
    # 确保 URL 以 http 开头
    if not url.startswith("http"):
        # 简单的容错
        if url.startswith("www"):
            url = "https://" + url
        else:
             return f"Error: Invalid URL format: {url}. URL must start with http:// or https://"

    async def _crawl():
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(url=url, bypass_cache=bypass_cache)
            if result.success:
                return result.markdown
            else:
                return f"Error: {result.error_message}"

    try:
        logger.info(f"[WebTools] Crawling URL: {url} (Bypass Cache: {bypass_cache})")
        content = _run_coro_sync(_crawl(), timeout=60)
        if content.startswith("Error"):
            logger.error(f"[WebTools] Crawl internal error: {content}")
            return content
            
        # [New] 文档落地 (Staging)
        # 将抓取的内容保存到 e:\xingchen-V\storage\knowledge_staging
        staging_dir = os.path.join(settings.PROJECT_ROOT, "storage", "knowledge_staging")
        os.makedirs(staging_dir, exist_ok=True)
        
        # 生成文件名 (Hash + Timestamp)
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawl_{timestamp}_{url_hash}.md"
        filepath = os.path.join(staging_dir, filename)
        
        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Source: {url}\n")
            f.write(f"# Date: {timestamp}\n\n")
            f.write(content)
            
        logger.info(f"[WebTools] Crawl successful. Saved to {filepath} ({len(content)} chars).")
        
        # 返回摘要和路径
        summary = content[:500] + "..." if len(content) > 500 else content
        return (
            f"✅ 抓取成功。\n"
            f"📍 原始文档已保存至: {filepath}\n"
            f"📄 内容摘要 (前500字):\n"
            f"{summary}\n\n"
            f"(S-Brain 请注意：完整内容已归档，请在反思周期中读取此文件进行内化。)"
        )
            
    except Exception as e:
        logger.error(f"[WebTools] Crawl failed: {e}", exc_info=True)
        return f"Exception: {str(e)}"
