import asyncio
import requests
from xingchen.tools.registry import ToolRegistry, ToolTier
from xingchen.utils.logger import logger

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


@ToolRegistry.register(
    name="web_search",
    description="在互联网上搜索信息 (自动适配国内外引擎)。",
    tier=ToolTier.SLOW,
    schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "max_results": {"type": "integer", "description": "返回结果数量", "default": 5}
        },
        "required": ["query"]
    }
)
def web_search(query: str, max_results: int = 5):
    # 1. 尝试 DuckDuckGo (国际化最优)
    if DDGS_AVAILABLE:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if results:
                    formatted = ""
                    for i, r in enumerate(results):
                        formatted += f"{i+1}. [{r['title']}]({r['href']})\n   {r['body']}\n\n"
                    return formatted
        except Exception as e:
            logger.warning(f"[WebTools] DuckDuckGo failed: {e}, falling back to domestic.")

    # 2. 尝试搜狗
    res = _sogou_search(query, max_results)
    if res: return res

    # 3. 尝试百度
    res = _baidu_search(query, max_results)
    if res: return res

    return "Error: 搜索服务暂不可用，请稍后再试。"


@ToolRegistry.register(
    name="web_crawl",
    description="抓取特定网页的全文内容并转为 Markdown 格式。需要完整的 URL。",
    tier=ToolTier.SLOW,
    schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "目标网页 URL"}
        },
        "required": ["url"]
    }
)
def web_crawl(url: str):
    if not CRAWL4AI_AVAILABLE:
        return "Error: 系统未安装网页抓取组件 (crawl4ai)。"

    async def _crawl():
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return result.markdown if result.success else f"Error: {result.error_message}"

    try:
        return asyncio.run(_crawl())
    except Exception as e:
        return f"Error: 抓取失败 - {str(e)}"
