---
name: web_search
description: [Tool] 网络搜索工具 (DuckDuckGo)。支持获取搜索结果摘要。
---

# Web Search (网络搜索)

这是一个内置的搜索工具，用于在互联网上查找信息。
它已经集成在 Driver (F-Brain) 的工具箱中。

## 能力
- 能够搜索关键词并返回 Top N 结果。
- 能够获取结果的标题、链接和简短摘要。
- 适合用于：发现新知识、查找资料来源、回答未知问题。

## 如何使用 (对于 S-Brain)
这是一个 **Driver 工具**。
S-Brain 应该建议 Driver 使用此工具来获取信息。

**指令示例**：
> "建议使用 web_search 工具搜索 'Python AsyncIO tutorial'，以获取学习资料。"
> "Driver, 请帮我搜索一下 'DeepSeek R1 paper'，我想看看它的原理。"

## 参数
- `query`: 搜索关键词 (必填)
- `max_results`: 结果数量 (默认 5)
