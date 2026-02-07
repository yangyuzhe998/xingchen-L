---
name: web_crawl
description: [Tool] 深度网页抓取工具 (Crawl4AI)。支持抓取动态网页、微信公众号、知乎等。
---

# Web Crawl (网页抓取)

这是一个内置的高级工具，用于获取网页的 Markdown 内容。
它已经集成在 Driver (F-Brain) 的工具箱中。

## 能力
- 能够处理 JavaScript 渲染的页面 (SPA)。
- 能够自动提取主要内容为 Markdown。
- 适合用于：深度阅读文章、获取新闻详情、资料调研。

## 如何使用 (对于 S-Brain)
这是一个 **Driver 工具**。
你 (Navigator/S-Brain) 不需要直接运行代码，只需要在 `suggestion` 或 `proactive_instruction` 中明确指示 Driver 使用此工具即可。

**指令示例**：
> "建议使用 web_crawl 工具读取 https://example.com 的内容，以获取更详细的信息。"
> "Driver, 请帮我抓取 https://github.com/microsoft/vscode 的页面，我想分析一下它的最新特性。"

## 参数
- `url`: 目标网页地址 (必填)
- `bypass_cache`: 是否强制刷新 (可选, 默认 False)
