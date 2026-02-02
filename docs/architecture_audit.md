# System Architecture Audit & Gap Analysis
**Date:** 2026-02-02
**Version:** 1.0
**Scope:** Core, Memory, Psyche, Skills, Tools

## 1. System Overview (Architecture)

The system follows a **Dual-Brain Architecture** (F-Brain/Driver + S-Brain/Navigator) centered around an **Event Bus** and **Shared Memory**.

*   **F-Brain (Driver)**: Reactive, tool-using, short-term focus. Powered by Qwen.
*   **S-Brain (Navigator)**: Reflective, long-term planning, diary writing, psyche updating. Powered by DeepSeek-Reasoner (R1).
*   **CycleManager**: The "Heartbeat" that coordinates the two brains, triggering S-Brain based on message counts or emotional spikes.
*   **MindLink**: A shared subconscious buffer allowing S-Brain to inject intuition into F-Brain's next cycle.
*   **Memory**: Hybrid system with ChromaDB (Vector) for long-term/skills and JSON for configuration.

## 2. Module Analysis & Findings

### 2.1 Core Modules
*   **Driver (`src/core/driver.py`)**:
    *   **Pros**: Clear separation of concerns. Uses `MindLink` and `PsycheState` effectively.
    *   **Cons**:
        *   Prompt construction (`DRIVER_SYSTEM_PROMPT.format(...)`) is rigid.
        *   Tool execution loop (3 retries) is basic.
        *   Hardcoded `search_skills` logic inside `think` method (should be more dynamic).
*   **Navigator (`src/core/navigator.py`)**:
    *   **Pros**: Advanced "Static Context" scanning allows self-awareness of code changes. "Dual Memory Compression" (Diary + Fact Extraction) is powerful.
    *   **Cons**:
        *   **Scalability**: `_build_static_context` scans *all* `.py` files in `src/`. As the project grows, this will exceed context windows. Need a "Context Selector" or "Summary" mechanism.
        *   **Parsing**: The output parsing for `delta` and `suggestion` relies on fragile string matching/regex.
*   **CycleManager (`src/core/cycle_manager.py`)**:
    *   **Pros**: Good event-driven design.
    *   **Cons**:
        *   `_idle_monitor_loop` polls every 60s. This might be too aggressive for a desktop assistant (creating log noise).
*   **EventBus (`src/core/bus.py`)**:
    *   **Pros**: SQLite-based persistence is robust.
    *   **Cons**:
        *   **Threading**: Spawns a new thread for *every* subscriber notification. High load could cause thread explosion.
        *   **Typing**: `payload` is `Dict[str, Any]`, making it hard to validate event structures.

### 2.2 Memory & Psyche
*   **Memory (`src/memory/memory_core.py`)**:
    *   **Pros**: Clean ChromaDB integration.
    *   **Cons**:
        *   Dependency Injection: Uses `set_navigator` to avoid circular imports.
        *   `add_short_term` compaction logic (Sliding Window) needs verification (was cut off in read).
*   **Psyche (`src/psyche/psyche_core.py`)**:
    *   **Pros**: 4D State + Stimulus-Decay model is implemented and working.
    *   **Cons**:
        *   `_generate_narrative_rule_based` is likely a placeholder.
        *   Decay rate is hardcoded (`0.05`).

### 2.3 Tools & Skills
*   **Skills (`src/skills/`)**:
    *   `LibraryManager` handles `SKILL.md` (Markdown) indexing.
    *   `SkillLoader` is a placeholder for Python-based skills.
    *   **Status**: Good separation, but `SkillLoader` is currently unused.
*   **Tools (`src/tools/`)**:
    *   Registry system is simple and effective.
    *   **Security Risk**: `run_shell_command` allows arbitrary execution. Need strict allowlist or sandbox.

## 3. Identified Gaps & Refactoring Plan

| ID | Module | Issue | Severity | Proposed Action |
|----|--------|-------|----------|-----------------|
| **G01** | Navigator | Context Scalability | High | Implement `ContextManager` to select only relevant files for S-Brain, or use file summaries. |
| **G02** | Bus | Thread Safety | Medium | Use `ThreadPoolExecutor` for event subscribers instead of `new Thread()`. |
| **G03** | Tools | Shell Security | High | Restrict `run_shell_command` to specific safe commands or require explicit user confirmation for *all* calls (currently only via prompt). |
| **G04** | Driver | Prompt Rigidity | Medium | Move prompt templates to `src/config/prompts.py` (partially done) and use a template engine (Jinja2) for complex logic. |
| **G05** | Psyche | Hardcoded Params | Low | Move decay rates and sensitivities to `src/config/settings.py`. |
| **G06** | Skill | Legacy Code | Low | Decide whether to keep `SkillLoader` or merge it into `LibraryManager`. |

## 4. Next Steps
1.  **Refactor EventBus**: Implement ThreadPool.
2.  **Harden Tools**: Add safety checks to `run_shell_command`.
3.  **Optimize Navigator**: Limit context loading.
