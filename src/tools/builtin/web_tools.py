

import asyncio
import requests
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
    logger.info("[WebTools] duckduckgo-search not available, using domestic search engines.")

# Check for BeautifulSoup
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("[WebTools] beautifulsoup4 not installed. Domestic search will be limited.")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def _sogou_search(query: str, max_results: int = 5) -> str:
    """使用搜狗搜索 (国内直连，无需 API Key)"""
    if not BS4_AVAILABLE:
        return None
    try:
        url = f"https://www.sogou.com/web?query={requests.utils.quote(query)}"
        resp = requests.get(url, headers=_HEADERS, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        for item in soup.select("div.vrwrap"):
            a = item.select_one("h3 a") or item.select_one("a")
            # 搜狗的摘要在 p.star-wiki 或 div.space-txt 或 p 标签内
            snippet = item.select_one("p.star-wiki") or item.select_one("div.space-txt") or item.select_one("p")

            if a:
                title = a.get_text(strip=True)
                href = a.get("href", "")
                body = snippet.get_text(strip=True) if snippet else ""
                results.append({"title": title, "href": href, "body": body})

            if len(results) >= max_results:
                break

        if not results:
            return None

        formatted = ""
        for i, r in enumerate(results):
            formatted += f"{i+1}. [{r['title']}]({r['href']})\n   {r['body']}\n\n"
        return formatted

    except Exception as e:
        logger.warning(f"[WebTools] Sogou search failed: {e}")
        return None


def _baidu_search(query: str, max_results: int = 5) -> str:
    """使用百度搜索 (国内直连备选)"""
    if not BS4_AVAILABLE:
        return None
    try:
        url = f"https://www.baidu.com/s?wd={requests.utils.quote(query)}&rn={max_results}"
        resp = requests.get(url, headers=_HEADERS, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        for item in soup.select("div.c-container"):
            a = item.select_one("h3 a")
            snippet = item.select_one("span.content-right_8Zs40") or item.select_one("div.c-abstract") or item.select_one("p")

            if a:
                title = a.get_text(strip=True)
                href = a.get("href", "")
                body = snippet.get_text(strip=True) if snippet else ""
                results.append({"title": title, "href": href, "body": body})

            if len(results) >= max_results:
                break

        if not results:
            return None

        formatted = ""
        for i, r in enumerate(results):
            formatted += f"{i+1}. [{r['title']}]({r['href']})\n   {r['body']}\n\n"
        return formatted

    except Exception as e:
        logger.warning(f"[WebTools] Baidu search failed: {e}")
        return None


def _ddg_search(query: str, max_results: int = 5) -> str:
    """使用 DuckDuckGo 搜索 (需要翻墙)"""
    if not DDGS_AVAILABLE:
        return None
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return None

        formatted = ""
        for i, r in enumerate(results):
            formatted += f"{i+1}. [{r['title']}]({r['href']})\n   {r['body']}\n\n"
        return formatted
    except Exception as e:
        logger.warning(f"[WebTools] DuckDuckGo search failed: {e}")
        return None


@ToolRegistry.register(
    name="web_search",
    description="[国内可用] 网络搜索。优先搜狗，备选百度/DuckDuckGo。",
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
    智能搜索：搜狗 → 百度 → DuckDuckGo 逐级降级。
    """
    logger.info(f"[WebTools] Searching for: {query} (Max: {max_results})")

    # 策略: 搜狗优先 → 百度备选 → DuckDuckGo 最后
    for name, fn in [("Sogou", _sogou_search), ("Baidu", _baidu_search), ("DuckDuckGo", _ddg_search)]:
        result = fn(query, max_results)
        if result:
            logger.info(f"[WebTools] ✅ {name} search succeeded.")
            return result
        logger.info(f"[WebTools] {name} unavailable, trying next...")

    return f"搜索失败：所有搜索引擎均无法获取结果。请检查网络连接。(Query: {query})"

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
