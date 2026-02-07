---
name: read_document
description: [Tool] 文档阅读工具。用于 S-Brain 深度阅读本地知识库 (Staging) 中的长文档。
---

# Read Document (深度文档阅读)

这是一个内置的 I/O 工具，允许 Driver 读取本地文件系统中的文档内容，并将其“上传”到当前对话的上下文中。

## 核心用途 (对于 S-Brain)
当 `web_crawl` 抓取了长文章并保存到 `storage/knowledge_staging` 后，S-Brain 可以使用此工具来读取文件的完整内容（或片段），以便进行深度反思、总结或提取知识。

**S-Brain 指令示例**：
> "Driver，请读取刚才抓取的文件 `e:\xingchen-V\storage\knowledge_staging\crawl_20260207_xxxx.md`，我想分析里面的技术细节。"

## 参数
- `file_path`: 文件的绝对路径 (必填)
- `start_line`: 起始行号 (默认 0)
- `end_line`: 结束行号 (默认 2000，防止 Context 溢出)

## 提示
- 由于 LLM 上下文限制，如果文件极长，建议分段读取。
- 读取的内容会被直接插入到对话历史中，DeepSeek 模型将能够像处理“上传文件”一样处理这些文本。
