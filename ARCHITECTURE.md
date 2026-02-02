# XingChen-V System Architecture

## 1. Core Philosophy: Dual Brain Bus Architecture
XingChen-V operates on a **Dual Brain** system connected by an asynchronous **Event Bus**. This design mimics the human cognitive process of "Fast Thinking" (System 1) and "Slow Thinking" (System 2).

### 🧠 F-Brain (Driver) - Fast Thinking
- **File**: [`src/core/driver.py`](src/core/driver.py)
- **Model**: Qwen (通义千问)
- **Role**: Handles real-time user interaction, short-term decision making, and tool execution.
- **Behavior**: Synchronous, low-latency. It acts immediately on user input but consults the S-Brain's latest "Suggestion" as a subconscious guide.
- **Persona**: A "Tsundere" (傲娇) girl, influenced by the dynamic `Psyche` state.

### 🧭 S-Brain (Navigator) - Slow Thinking
- **File**: [`src/core/navigator.py`](src/core/navigator.py)
- **Model**: DeepSeek R1 (Reasoner)
- **Role**: Deep reflection, long-term planning, memory compression, and self-evolution.
- **Behavior**: Asynchronous, background execution. It analyzes the `EventBus` history to generate insights (`navigator_suggestion`) and updates the system's mental state.
- **Key Feature**: **Dual Memory Compression**
  - **Creative Mode**: Writes a fun, character-driven diary to [`src/memory/diary.md`](src/memory/diary.md).
  - **Fact Mode**: Extracts pure facts into the Vector DB (ChromaDB).
  - **Optimization**: Uses `threading.Lock` for concurrency safety and runs silently in the background.

## 2. Nervous System: Event Bus & Cycle Manager

### 🚌 Event Bus
- **File**: [`src/core/bus.py`](src/core/bus.py)
- **Technology**: SQLite-based persistent queue.
- **Function**: Decouples the Driver and Navigator. Every action (User Input, Driver Response, System Notification) is an event.
- **Schema**: `type`, `source`, `payload` (JSON), `meta` (JSON), `timestamp`.

### 💓 Cycle Manager
- **File**: [`src/core/cycle_manager.py`](src/core/cycle_manager.py)
- **Role**: The "Pacemaker". It monitors the Event Bus and triggers the S-Brain based on:
  1. **Token/Turn Count**: After N rounds of conversation.
  2. **Emotion Spikes**: If the user shows strong emotions (anger, fear).
  3. **Idle Time**: If the system is idle for too long (prevents "brain death").

## 3. Memory System
- **File**: [`src/memory/memory_core.py`](src/memory/memory_core.py)
- **Structure**:
  - **Short-Term**: RAM-based sliding window of recent messages.
  - **Long-Term (Vector)**: ChromaDB for semantic search of facts.
  - **Long-Term (Storage)**: JSON file for structured data.
  - **Diary**: Markdown file for episodic memory and persona maintenance.

## 4. Evolution Engine (Self-Improvement)
- **File**: [`src/core/evolution_manager.py`](src/core/evolution_manager.py)
- **Strategy**: **MCP First** (Model Context Protocol).
- **Process**:
  1.  **Request**: S-Brain identifies a missing skill (e.g., "I need to search GitHub").
  2.  **Search**: Uses Puppeteer/WebSearch to find an existing MCP Server config on GitHub.
  3.  **Load**: Dynamically loads the MCP tool if found.
  4.  **Fallback**: Generates Python code (Single file or Docker package) if no MCP is found.

## 5. Skill System
- **Registry**: [`src/tools/registry.py`](src/tools/registry.py) - Central lookup for all tools.
- **Loader**: [`src/skills/loader.py`](src/skills/loader.py) - Hot-swaps skills from `src/skills/`.
- **Tiers**:
  - **FAST**: Local, zero-cost (e.g., `get_time`, `calculate`).
  - **SLOW**: Network/Compute heavy, usually MCP or Docker-based.

## 6. Social & Psyche
- **Psyche**: [`src/psyche/psyche_core.py`](src/psyche/psyche_core.py) - 4-dimensional emotional state (Curiosity, Interest, Morality, Fear).
- **Moltbook**: [`src/social/moltbook_client.py`](src/social/moltbook_client.py) - External social network interface with its own heartbeat loop.
