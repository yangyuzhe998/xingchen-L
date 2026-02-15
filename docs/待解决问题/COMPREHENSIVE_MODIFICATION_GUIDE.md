# 星辰-V 全面修改指南

> **创建日期**: 2026-02-15
> **版本基线**: v2.3
> **分析范围**: `src/` 下全部 50+ Python 文件，涵盖所有模块

本文档按模块逐一列出所有发现的问题，并附上具体的修改方案。每个问题标注了**优先级**和**难度**，方便你按顺序执行。

---

## 目录

- [P0 - 必须立即修复的 Bug](#p0---必须立即修复的-bug)
- [P1 - 核心模块加强](#p1---核心模块加强)
- [P2 - 架构层面改进](#p2---架构层面改进)
- [P3 - 细节打磨与代码质量](#p3---细节打磨与代码质量)
- [P4 - 功能增强建议](#p4---功能增强建议)

---

## P0 - 必须立即修复的 Bug

### BUG-01: Driver 主动发言事件发布缩进错误

| 属性 | 值 |
|------|-----|
| **文件** | `src/core/driver/engine.py` |
| **行号** | 第 103 行 |
| **严重性** | 🔴 严重 |
| **难度** | ⭐ 简单 |

**问题**: `event_bus.publish(...)` 代码块的缩进少了一级，导致无论 `reply` 是否存在，事件都会被发布。这意味着即使 AI 没有生成回复（`reply` 为 None 或空），也会向前端推送一个空消息。

**当前代码** (有问题):
```python
            if reply:
                # ... 正常处理
                self.memory.add_short_term("assistant", reply)
                
                # 发布事件
            event_bus.publish(Event(  # ← 这行缩进错了，应该在 if reply: 里面
```

**修改方案**:
```python
            if reply:
                logger.info(f"[{self.name}] (主动): {reply}")
                self.memory.add_short_term("assistant", reply)
                
                # 发布事件 (注意缩进！)
                event_bus.publish(Event(
                    type="driver_response",
                    source="driver",
                    payload=DriverResponsePayload(content=reply),
                    meta={
                        "inner_voice": inner_voice,
                        "user_emotion_detect": emotion,
                        "proactive": True
                    }
                ))
```

---

### BUG-02: system_tools.py 函数重复定义

| 属性 | 值 |
|------|-----|
| **文件** | `src/tools/builtin/system_tools.py` |
| **行号** | 第 109 行 和 第 168 行 |
| **严重性** | 🔴 严重 |
| **难度** | ⭐ 简单 |

**问题**: `read_skill` 函数被定义了两次。第168行的定义覆盖了第109行带安全检查的版本。第168行的版本没有任何安全检查，直接调用 `library_manager.checkout_skill(path)`。

**修改方案**: 删除第 168-169 行的重复定义。保留第109行带安全检查的版本。

```diff
-def read_skill(path: str):
-    return library_manager.checkout_skill(path)
```

---

### BUG-03: Driver._think_internal 中 print 和 logger 混用

| 属性 | 值 |
|------|-----|
| **文件** | `src/core/driver/engine.py` |
| **行号** | 第 155, 182, 192, 312, 319, 322, 356 行 |
| **严重性** | 🟡 中等 |
| **难度** | ⭐ 简单 |

**问题**: `_think_internal` 方法中大量使用 `print()` 而不是 `logger`。这导致：
1. Web 模式下这些信息不会出现在日志文件中
2. 日志级别无法控制
3. 格式不统一

**修改方案**: 将所有 `print(f"[{self.name}]...")` 替换为对应的 `logger.info()` 或 `logger.debug()`：

```python
# 第155行
# 之前: print(f"[{self.name}] 正在思考: {user_input}")
logger.info(f"[{self.name}] 正在思考: {user_input}")

# 第182行
# 之前: print(f"[{self.name}] 🔍 检测到模糊别名: ...")
logger.info(f"[{self.name}] 🔍 检测到模糊别名: '{alias}' -> '{target}' (dist: {dist:.4f})")

# 第192行
# 之前: print(f"[{self.name}] 别名检索异常: {e}")
logger.warning(f"[{self.name}] 别名检索异常: {e}")

# 第312行
# 之前: print(f"[{self.name}] 🛠️ 正在调用工具: ...")
logger.info(f"[{self.name}] 🛠️ 正在调用工具: {function_name} Args: {function_args}")

# 第97行 (proactive_speak)
# 之前: print(f"\n[{self.name}] (主动): {reply}")
# 改为仅保留 logger (CLI 显示由 EventBus 事件触发)
```

---

## P1 - 核心模块加强

### P1-01: LLMClient 缺少重试机制

| 属性 | 值 |
|------|-----|
| **文件** | `src/utils/llm_client.py` |
| **模块** | Utils |
| **难度** | ⭐⭐ 中等 |

**问题**: `chat()` 方法在 API 调用失败时直接返回 `None`，没有任何重试逻辑。网络波动、API 限流等常见情况会直接导致功能中断。

**修改方案**:
```python
import time

def chat(self, messages, temperature=0.7, trace_id=None, tools=None, 
         tool_choice=None, max_retries=2):
    """发送消息给 LLM，支持自动重试"""
    if not trace_id:
        trace_id = str(uuid.uuid4())[:8]

    for attempt in range(max_retries + 1):
        try:
            # ... 现有调用逻辑 ...
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message if tools else response.choices[0].message.content
            
        except Exception as e:
            if attempt < max_retries:
                wait_time = 2 ** attempt  # 指数退避: 1s, 2s
                logger.warning(f"[{self.provider}] 第{attempt+1}次调用失败，{wait_time}s 后重试: {e}")
                time.sleep(wait_time)
            else:
                logger.error(f"[{self.provider}] 已达到最大重试次数({max_retries}): {e}", exc_info=True)
                return None
```

---

### P1-02: PsycheEngine 规则引擎过于简陋

| 属性 | 值 |
|------|-----|
| **文件** | `src/psyche/core/engine.py` |
| **模块** | Psyche |
| **难度** | ⭐⭐⭐ 较难 |

**问题**: `_generate_narrative_rule_based()` 方法仅用简单的 if/else 判断数值区间来生成叙事，缺乏维度之间的交互作用，且不支持复合情绪。

**当前不足**:
1. 维度独立：恐惧高 + 好奇心高 = 只输出两条独立描述，不会产生"紧张性好奇"这种复合情绪
2. 没有情绪历史：不记录情绪变化趋势
3. 亲密度变化太机械：`_think_internal` 中每次交互硬编码 +0.01

**修改方案（分两步）**:

**第一步 - 简单改进（不增加复杂度）**:
```python
def _generate_narrative_rule_based(self) -> str:
    d = self.state["dimensions"]
    fear = d["fear"]["value"]
    laziness = d["laziness"]["value"]
    curiosity = d["curiosity"]["value"]
    survival = d["survival"]["value"]
    intimacy = d.get("intimacy", {}).get("value", 0.1)
    
    # 计算主导情绪 (取最偏离基线的维度)
    deviations = {}
    for key, dim in d.items():
        deviations[key] = abs(dim["value"] - dim["baseline"])
    dominant = max(deviations, key=deviations.get)
    
    narrative = []
    
    # ====== 复合情绪规则 ======
    if fear > 0.6 and curiosity > 0.6:
        narrative.append("内心矛盾：既感到不安，又被未知吸引——像在黑暗中好奇地探路。")
    elif fear > 0.6 and laziness > 0.6:
        narrative.append("想逃避但又提不起干劲，只想蜷缩起来等风暴过去。")
    elif curiosity > 0.7 and laziness < 0.3:
        narrative.append("精力充沛，对一切都跃跃欲试。")
    else:
        # 保留现有的单维度判断逻辑
        # ...
    
    # ====== 亲密度（不变）======
    # ...
    
    # ====== 新增：情绪趋势 ======
    # 比较当前值与上一次记录的差异方向
    # (需要在 state 中新增 "previous_dimensions" 字段)
    
    return " ".join(narrative)
```

**第二步 - 移除硬编码亲密度增长** (`engine.py` 第162行):
```python
# 之前: psyche_engine.update_state({"intimacy": 0.01})  # 每次交互固定+0.01
# 改为: 由 S脑 分析情感后决定亲密度变化
# 删除这一行，亲密度变化应完全由 Reasoner 的 psyche_delta 驱动
```

---

### P1-03: MindLink 缺少直觉衰减机制

| 属性 | 值 |
|------|-----|
| **文件** | `src/psyche/services/mind_link.py` |
| **模块** | Psyche |
| **难度** | ⭐⭐ 中等 |

**问题**: 代码注释（第79行）提到"可以加入衰减逻辑：如果直觉太旧了（比如超过1小时），是否还生效？"但没有实现。当前行为是直觉永不过期，即使是数天前的直觉也会一直影响 F脑。

**修改方案**:
```python
def read_intuition(self) -> str:
    """[F-Brain Read] 读取直觉 (带衰减)"""
    with self._lock:
        intuition = self._buffer.get("intuition", "")
        timestamp = self._buffer.get("timestamp", 0)
        
        # 衰减逻辑：直觉超过 1 小时后，强度自然降低
        age_seconds = time.time() - timestamp
        
        if age_seconds > 3600:  # 超过 1 小时
            # 返回弱化版本的直觉
            return f"(模糊的直觉) {intuition}" if intuition else ""
        elif age_seconds > 7200:  # 超过 2 小时
            # 直觉几乎消散
            return "保持观察，暂无强烈直觉。"
        
        return intuition
```

---

### P1-04: ChromaStorage 初始化失败后无恢复能力

| 属性 | 值 |
|------|-----|
| **文件** | `src/memory/storage/vector.py` |
| **模块** | Memory |
| **难度** | ⭐⭐ 中等 |

**问题**: 如果 ChromaDB 初始化失败（例如数据库文件损坏），`self.client` 和所有 collection 都是 `None`，但后续所有调用方都没有检查这种情况，会直接抛错。

**修改方案**:
```python
class ChromaStorage:
    def __init__(self, db_path):
        self.client = None
        self.collection = None
        self.skill_collection = None
        self._available = False  # 新增: 可用性标志
        
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            # ... 现有初始化逻辑 ...
            self._available = True
            logger.info("[Memory] ChromaDB 初始化成功。")
        except Exception as e:
            logger.error(f"[Memory] ChromaDB 初始化失败: {e}")
            logger.warning("[Memory] 向量检索功能将不可用，系统将以降级模式运行。")
    
    def get_memory_collection(self):
        if not self._available:
            return None  # 调用方已经有 None 检查
        return self.collection
```

---

### P1-05: 测试覆盖严重不足

| 属性 | 值 |
|------|-----|
| **位置** | `tests/` |
| **模块** | 测试 |
| **难度** | ⭐⭐⭐ 较难（工作量大） |

**问题**: 核心模块几乎没有单元测试。

**当前测试覆盖**:
| 模块 | 测试文件 | 状态 |
|------|----------|------|
| EventBus | `test_core/test_event_bus.py` | ✅ 有 |
| Memory Storage | `test_memory/` (7个文件) | ✅ 有 |
| Utils | `test_utils/` (4个文件) | ✅ 有 |
| Config | `test_config/` (2个文件) | ✅ 有 |
| **Driver** | 无 | ❌ 缺失 |
| **Navigator** | 无 | ❌ 缺失 |
| **CycleManager** | 无 | ❌ 缺失 |
| **PsycheEngine** | 无 | ❌ 缺失 |
| **MindLink** | 无 | ❌ 缺失 |
| **ToolRegistry** | 无 | ❌ 缺失 |

**修改方案**: 按以下优先级添加测试（每个给出核心测试点）：

**1. PsycheEngine (最简单，无外部依赖)**
```python
# tests/test_core/test_psyche.py
def test_update_state_clamps_values():
    """验证状态值始终在 0.0-1.0 之间"""
    
def test_decay_toward_baseline():
    """验证每次更新后值向基线回归"""
    
def test_sensitivity_affects_change():
    """验证 sensitivity 系数正确生效"""
```

**2. MindLink**
```python
# tests/test_core/test_mind_link.py
def test_inject_and_read():
    """验证注入的直觉可以被正确读取"""
    
def test_persistence():
    """验证重启后能恢复直觉"""
```

**3. ToolRegistry**
```python
# tests/test_tools/test_registry.py
def test_register_and_execute():
    """验证工具注册后能正常执行"""
    
def test_tier_filter():
    """验证按层级过滤工具"""
```

**4. Driver (需要 Mock LLM)**
```python
# tests/test_core/test_driver.py
def test_think_basic_response(mock_llm):
    """Mock LLM 返回，验证基本对话流程"""
    
def test_tool_call_loop(mock_llm):
    """验证工具调用循环"""
```

---

## P2 - 架构层面改进

### P2-01: Driver._think_internal 方法过长（246行）

| 属性 | 值 |
|------|-----|
| **文件** | `src/core/driver/engine.py` |
| **行号** | 第 154-399 行 |
| **模块** | Core |
| **难度** | ⭐⭐ 中等 |

**问题**: `_think_internal` 承担了太多职责：
1. 心智更新
2. 读取潜意识
3. 长期记忆检索
4. 别名解析
5. 用户画像检索
6. 技能搜索
7. 工具列表构建
8. Prompt 组装
9. LLM 调用 + 工具循环
10. 响应解析
11. 事件发布

**修改方案**: 拆分为子方法，不需要改变外部接口：

```python
def _think_internal(self, user_input, psyche_state=None, suggestion=""):
    # 1. 准备上下文
    context = self._prepare_context(user_input)
    
    # 2. 组装 Prompt
    messages = self._build_messages(user_input, context)
    
    # 3. 调用 LLM (含工具循环)
    raw_response = self._call_llm_with_tools(messages)
    
    # 4. 解析响应
    reply, inner_voice, emotion = self._parse_response(raw_response)
    
    # 5. 存储 & 发布
    self._finalize(user_input, reply, inner_voice, emotion, psyche_state, suggestion)
    
    return reply

def _prepare_context(self, user_input):
    """准备所有上下文信息"""
    return {
        "psyche": psyche_engine.get_state_summary(),
        "intuition": mind_link.read_intuition(),
        "long_term": self._get_enriched_long_term(user_input),
        "skills": self._search_relevant_skills(user_input),
        "tools": self._build_tool_list(),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
```

---

### P2-02: 全局单例过多，测试困难

| 属性 | 值 |
|------|-----|
| **文件** | 多个 |
| **模块** | 架构 |
| **难度** | ⭐⭐⭐ 较难 |

**问题**: 以下组件使用了全局单例或模块级实例化：
- `event_bus` (event_bus.py 第179行)
- `psyche_engine`, `mind_link` (psyche/__init__.py)
- `knowledge_db` (knowledge_db.py 第31行)
- `tool_registry` (registry.py 第102行)
- `memory_orchestrator` (memory_orchestrator.py 第136行)
- `auto_classifier` (auto_classifier.py 第178行)
- `topic_manager` (topic_manager.py)
- `library_manager`, `settings`

这导致单元测试时几乎无法隔离依赖，因为导入任何模块都会触发全链初始化。

**修改方案（渐进式）**:
1. **短期**: 在 `conftest.py` 中使用 `monkeypatch` 替换全局单例
2. **中期**: 引入工厂函数，将单例创建延迟到需要时
3. **长期**: 引入一个简单的依赖容器类

短期方案示例：
```python
# tests/conftest.py

@pytest.fixture
def mock_event_bus(monkeypatch):
    """替换全局 EventBus 为测试版本"""
    from unittest.mock import MagicMock
    mock_bus = MagicMock()
    monkeypatch.setattr("src.core.bus.event_bus.event_bus", mock_bus)
    return mock_bus
```

---

### P2-03: web_crawl 的 asyncio.run() 冲突

| 属性 | 值 |
|------|-----|
| **文件** | `src/tools/builtin/web_tools.py` |
| **行号** | 第 112 行 |
| **模块** | Tools |
| **难度** | ⭐⭐ 中等 |

**问题**: `web_crawl` 使用 `asyncio.run(_crawl())`，但如果在 Web 模式下（Uvicorn），已经有一个运行中的事件循环，`asyncio.run()` 会抛出 `RuntimeError: This event loop is already running`。

**修改方案**:
```python
def web_crawl(url: str, bypass_cache: bool = False):
    # ... URL 清洗逻辑不变 ...

    async def _crawl():
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(url=url, bypass_cache=bypass_cache)
            return result.markdown if result.success else f"Error: {result.error_message}"

    try:
        # 检测是否已有运行中的 loop
        try:
            loop = asyncio.get_running_loop()
            # 如果有，使用 run_coroutine_threadsafe
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(_crawl(), loop)
            content = future.result(timeout=60)
        except RuntimeError:
            # 没有运行中的 loop，安全使用 asyncio.run
            content = asyncio.run(_crawl())
        
        # ... 后续文件保存逻辑不变 ...
```

---

## P3 - 细节打磨与代码质量

### P3-01: calculate 工具使用 eval()

| 属性 | 值 |
|------|-----|
| **文件** | `src/tools/builtin/system_tools.py` |
| **行号** | 第 41 行 |
| **模块** | Tools |
| **难度** | ⭐ 简单 |

**问题**: 虽然做了字符过滤，但 `eval()` 本质上不安全。当前过滤允许 `.`，理论上可以构造 `().__class__` 等利用字符。

**修改方案**: 使用 `ast.literal_eval` 或 Python 内置的 `compile` + 受限执行：
```python
import ast
import operator

# 安全计算器
SAFE_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.USub: operator.neg,
}

def safe_eval(expr):
    """安全的数学表达式求值"""
    tree = ast.parse(expr, mode='eval')
    return _eval_node(tree.body)

def _eval_node(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        op = SAFE_OPERATORS.get(type(node.op))
        if op is None: raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
        return op(_eval_node(node.left), _eval_node(node.right))
    elif isinstance(node, ast.UnaryOp):
        op = SAFE_OPERATORS.get(type(node.op))
        if op is None: raise ValueError(f"不支持的运算符")
        return op(_eval_node(node.operand))
    else:
        raise ValueError(f"不支持的表达式类型: {type(node).__name__}")
```

---

### P3-02: run_shell_command 缺少命令过滤

| 属性 | 值 |
|------|-----|
| **文件** | `src/tools/builtin/system_tools.py` |
| **行号** | 第 57-73 行 |
| **模块** | Tools |
| **难度** | ⭐⭐ 中等 |

**问题**: AI 可以执行任意 PowerShell 命令，包括删除文件、修改系统配置等危险操作。没有任何黑名单或确认机制。

**修改方案**: 添加命令黑名单 + 用户确认机制：
```python
DANGEROUS_COMMANDS = [
    "rm ", "del ", "remove-item", "format-", 
    "reg ", "net user", "shutdown", "restart",
    "rmdir", "rd "
]

def run_shell_command(command: str):
    command_lower = command.lower()
    for danger in DANGEROUS_COMMANDS:
        if danger in command_lower:
            return f"⚠️ 安全拦截: 命令包含危险关键词 '{danger}'。请通过手动终端执行。"
    
    # ... 原有执行逻辑 ...
```

---

### P3-03: MemoryService.search_alias 性能问题

| 属性 | 值 |
|------|-----|
| **文件** | `src/memory/services/memory_service.py` |
| **行号** | 第 95-131 行 |
| **模块** | Memory |
| **难度** | ⭐⭐ 中等 |

**问题**: 每次调用 `search_alias` 都会从 KnowledgeDB 加载所有实体到内存进行遍历匹配。数据量大时会严重影响每次对话的响应速度（因为每次 `_think_internal` 都会调用）。

**修改方案**: 在 MemoryService 初始化时一次性加载别名缓存，后续增量更新：
```python
class MemoryService:
    def __init__(self, ...):
        # ... 现有逻辑 ...
        self._alias_cache = {}  # alias -> target_name
        self._load_alias_cache()
    
    def _load_alias_cache(self):
        """一次性加载所有别名到内存"""
        try:
            all_entities = self.knowledge_db.get_all_entities()
            for entity in all_entities:
                name = entity['name']
                self._alias_cache[name] = name
                for alias in (entity.get('aliases') or []):
                    if alias:
                        self._alias_cache[alias] = name
        except Exception as e:
            logger.warning(f"[Memory] 别名缓存加载失败: {e}")
    
    def save_alias(self, alias, target_entity):
        # ... 原有逻辑 ...
        # 新增: 更新缓存
        self._alias_cache[alias.strip()] = target_entity
    
    def search_alias(self, query, limit=None, threshold=None):
        """使用缓存进行快速匹配"""
        matches = []
        for alias, target in self._alias_cache.items():
            if alias in query:
                matches.append((alias, target, len(alias)))
        
        if matches:
            matches.sort(key=lambda x: x[2], reverse=True)
            best = matches[0]
            return (best[0], best[1], 1.0)
        return None
```

---

### P3-04: DebugCLI 调试命令未实现

| 属性 | 值 |
|------|-----|
| **文件** | `src/ui/debug_app.py` |
| **行号** | 第 126-141 行 |
| **模块** | UI |
| **难度** | ⭐⭐ 中等 |

**问题**: `/dump_memory` 和 `/psyche` 命令只有框架，实际逻辑是 `pass`。

**修改方案**: 通过 EventBus 发送查询请求并打印结果：
```python
def _handle_debug_command(self, cmd: str):
    if cmd == "/help":
        print("Available Commands:")
        print("  /dump_memory  - 打印当前短期记忆")
        print("  /psyche       - 打印当前心智状态")
        print("  /force_s      - 强制触发 S 脑思考")
        print("  /stats        - 显示系统统计信息")
        
    elif cmd == "/psyche":
        from src.psyche import psyche_engine
        state = psyche_engine.get_raw_state()
        print(json.dumps(state, indent=2, ensure_ascii=False))
        
    elif cmd == "/dump_memory":
        # 通过 EventBus 请求记忆转储
        event_bus.publish(Event(
            type="debug_request",
            source="debug_cli",
            payload={"action": "dump_short_term"},
            meta={}
        ))
```

---

### P3-05: WebApp 未展示内心独白和心智状态

| 属性 | 值 |
|------|-----|
| **文件** | `src/ui/web_app.py` |
| **模块** | UI |
| **难度** | ⭐⭐ 中等 |

**问题**: `_on_bus_event` 方法收到 `driver_response` 事件时，`meta` 中已经包含 `inner_voice` 和 `user_emotion_detect`，但 `display_message` 只是把它们作为原始 meta 传给前端，前端也没有展示逻辑。

**修改方案**: 在 `_on_bus_event` 中增加系统提示推送：
```python
elif event_type == EventType.DRIVER_RESPONSE.value:
    # ... 现有内容提取 ...
    self.display_message("assistant", content, meta)
    
    # 推送内心独白（作为系统消息）
    inner_voice = meta.get('inner_voice', '')
    if inner_voice and inner_voice != "直接输出":
        self.display_message("system", f"💭 {inner_voice}", 
                            {"type": "inner_voice"})

elif event_type == EventType.NAVIGATOR_SUGGESTION.value:
    # 现有代码是 pass，应该推送给前端
    if suggestion:
        self.display_message("system", f"🧭 S脑直觉: {suggestion}",
                            {"type": "navigator_suggestion"})
```

---

### P3-06: json_parser 正则匹配可能错误

| 属性 | 值 |
|------|-----|
| **文件** | `src/utils/json_parser.py` |
| **行号** | 第 32 行 |
| **模块** | Utils |
| **难度** | ⭐⭐ 中等 |

**问题**: 正则 `r'(\{[\s\S]*\}|\[[\s\S]*\])'` 使用贪婪匹配，会匹配从第一个 `{` 到最后一个 `}` 之间的所有内容。如果文本中有多个 JSON 对象或混合内容，可能匹配错误。

**修改方案**: 使用更精确的括号匹配：
```python
def extract_json(text: str) -> Optional[Union[Dict, List]]:
    # 1. 直接解析 (不变)
    # 2. 清理代码块 (不变)
    
    # 3. 改进的 JSON 提取: 从第一个 { 或 [ 开始，逐字符计数括号
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start_idx = text.find(start_char)
        if start_idx == -1:
            continue
        
        depth = 0
        in_string = False
        escape = False
        
        for i in range(start_idx, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == '\\':
                escape = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == start_char:
                depth += 1
            elif c == end_char:
                depth -= 1
                if depth == 0:
                    candidate = text[start_idx:i+1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break
    return None
```

---

### P3-07: Driver.act() 方法是空壳

| 属性 | 值 |
|------|-----|
| **文件** | `src/core/driver/engine.py` |
| **行号** | 第 401-405 行 |
| **模块** | Core |
| **难度** | ⭐ 简单 |

**问题**: `act()` 方法只有一个 `print`，没有实际逻辑。如果不打算使用，应该明确标记或移除。

**修改方案**: 添加废弃标记或移除：
```python
def act(self, action):
    """执行具体行动。[Deprecated: 行动已通过工具系统执行]"""
    logger.warning(f"[{self.name}] act() 已废弃，请使用工具系统。Action: {action}")
```

---

### P3-08: Shell Manager 信任值更新未实现

| 属性 | 值 |
|------|-----|
| **文件** | `src/core/managers/shell_manager.py` |
| **行号** | 约 167 行 |
| **模块** | Core |
| **难度** | ⭐⭐ 中等 |

**问题**: `update_case_trust` 方法有 TODO 标记但未实现，导致命令执行的经验回放无法建立强化学习信号。

**修改方案**:
```python
def update_case_trust(self, case_id: str, delta: float):
    """更新案例信任值"""
    collection = self.memory.get_command_cases_collection()
    if not collection:
        return
    
    try:
        # 获取当前元数据
        result = collection.get(ids=[case_id], include=["metadatas"])
        if result and result["metadatas"]:
            meta = result["metadatas"][0]
            current_trust = meta.get("trust_score", 0.5)
            new_trust = max(0.0, min(1.0, current_trust + delta))
            meta["trust_score"] = new_trust
            collection.update(ids=[case_id], metadatas=[meta])
            logger.info(f"[ShellManager] 案例 {case_id} 信任值更新: {current_trust:.2f} -> {new_trust:.2f}")
    except Exception as e:
        logger.error(f"[ShellManager] 信任值更新失败: {e}")
```

---

## P4 - 功能增强建议

### P4-01: UI 接口抽象类未使用 ABC

| 属性 | 值 |
|------|-----|
| **文件** | `src/interfaces/ui_interface.py` |
| **模块** | Interface |
| **难度** | ⭐ 简单 |

**问题**: 注释说"不继承 ABC，避免与 Textual App 冲突"，但项目已经不使用 Textual。所有方法使用 `raise NotImplementedError` 而不是 `@abstractmethod`，这意味着忘记实现方法时不会在创建对象时报错，而是在运行时才发现。

**修改方案**: 改回 ABC：
```python
from abc import ABC, abstractmethod

class UserInterface(ABC):
    @abstractmethod
    def display_message(self, role, content, meta=None): ...
    
    @abstractmethod
    def set_input_handler(self, handler): ...
    
    @abstractmethod
    def update_status(self, status, details=None): ...
    
    @abstractmethod
    def run(self): ...
```

---

### P4-02: 主动对话冷却时间不够智能

| 属性 | 值 |
|------|-----|
| **文件** | `src/core/driver/engine.py` |
| **模块** | Core |
| **难度** | ⭐⭐ 中等 |

**问题**: 冷却时间是固定的 60 秒 (`PROACTIVE_COOLDOWN`)。白天应该更低（更活跃），深夜应该更高（别打扰人），应根据时间和心智状态动态调整。

**修改方案**:
```python
def _get_dynamic_cooldown(self):
    """根据时间和心智状态动态计算冷却时间"""
    base = settings.PROACTIVE_COOLDOWN
    hour = datetime.now().hour
    
    # 深夜 (23:00-7:00) 冷却翻倍
    if hour >= 23 or hour < 7:
        base *= 2
    
    # laziness 高时冷却增加
    laziness = psyche_engine.state["dimensions"]["laziness"]["value"]
    base *= (1 + laziness)
    
    return base
```

---

### P4-03: openclaw_temp 目录清理

| 属性 | 值 |
|------|-----|
| **位置** | `openclaw_temp/` |
| **模块** | 项目根目录 |
| **难度** | ⭐ 简单 |

**问题**: `openclaw_temp/` 目录包含大量外部项目文件（50+ 个 md 文件、完整的 app 结构），看起来像是复制过来参考用的，但没有被任何代码引用。占用空间且影响项目清洁度。

**修改方案**: 
1. 如果有参考价值，移动到 `docs/references/` 并只保留有用的文件
2. 如果已无用，加入 `.gitignore` 并删除

---

### P4-04: Driver 中 payload 类型不一致

| 属性 | 值 |
|------|-----|
| **文件** | `src/core/driver/engine.py` |
| **行号** | 第 106 行 vs 第 351 行 vs 第 390 行 |
| **模块** | Core |
| **难度** | ⭐ 简单 |

**问题**: 同样是发布 `driver_response` 事件，三处 payload 格式不一致：
- 第106行: `DriverResponsePayload(content=reply)` (Pydantic 模型)
- 第351行: `{"content": reply}` (普通字典)
- 第390行: `{"content": reply}` (普通字典)

**修改方案**: 统一使用 Pydantic 模型：
```python
# 所有发布 driver_response 的地方统一为:
event_bus.publish(Event(
    type="driver_response",
    source="driver",
    payload=DriverResponsePayload(content=reply),
    meta={...}
))
```

---

## 执行建议

### 推荐修改顺序

```
第一批（1-2天）: BUG-01, BUG-02, BUG-03, P3-07, P4-04
  → 修 Bug + 统一代码风格，零风险

第二批（2-3天）: P1-01, P1-03, P1-04, P3-06
  → 加固基础设施（LLM重试、MindLink衰减、ChromaDB保护、JSON解析）

第三批（3-5天）: P1-05
  → 补测试，为后续大改提供安全网

第四批（3-5天）: P1-02, P2-01
  → 升级心智引擎 + 重构 Driver

第五批（随时）: P3-01, P3-02, P3-03, P3-04, P3-05
  → 按需打磨细节
```

### 修改原则

1. **每次只改一个模块**: 改完跑一遍现有测试
2. **先写测试，再改代码**: 尤其是 P1-02（心智引擎）
3. **保留旧接口**: 用 `@deprecated` 标记而不是直接删除
4. **每个 PR 一个主题**: 别把修 Bug 和加功能混在一起
