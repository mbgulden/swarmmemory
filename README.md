# 🧠 SwarmMemory

[![CI](https://github.com/mbgulden/swarmmemory/actions/workflows/ci.yml/badge.svg)](https://github.com/mbgulden/swarmmemory/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Shared persistent memory for AI agent swarms**  
> *Episodic recall, versioned working scratchpads, and AST-based semantic context — pure Python stdlib, zero runtime dependencies.*

---

## 💡 Why SwarmMemory?

Multi-agent swarms (Prismatic agents, AutoGen crews, ad-hoc agent loops) are amnesiac by default:
- Agents forget what happened two tasks ago — decisions get re-litigated, bugs get re-introduced.
- Shared state gets clobbered when two agents write to the same place at the same time.
- Feeding a whole codebase into every agent's context is slow, expensive, and unnecessary.

**SwarmMemory** gives a swarm three kinds of memory that map directly to how agents actually work:
- **Episodic** — append-only event log with full-text recall ("what did the planner decide about the DB layer?").
- **Working** — a shared key-value scratchpad with versioned writes and compare-and-swap, so concurrent agents never silently overwrite each other.
- **Semantic** — on-demand AST distillation of a Python codebase into token-capped context ("give the reviewer the shape of this module").

---

## 🏛️ System Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │                 Agent swarm                  │
                    │      (planner, builder, reviewer, ...)       │
                    └──────┬──────────────┬─────────────┬─────────┘
                           │              │             │
              1. remember   │  2. share    │ 3. distill  │
                           ▼              ▼             ▼
              ┌───────────────┐ ┌──────────────┐ ┌──────────────┐
              │ EpisodicStore │ │   Working    │ │  Semantic    │
              │  SQLite +     │ │  Scratchpad  │ │  Distiller   │
              │  FTS5 recall  │ │  KV + CAS    │ │  AST of .py  │
              └───────┬───────┘ └──────┬───────┘ └──────┬───────┘
                      └───────────────┴───────────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │     MemoryIndex     │
                           │  search / stats /   │
                           │  export_context     │
                           └─────────────────────┘
```

---

## 📦 Installation

```bash
# From source
pip install git+https://github.com/mbgulden/swarmmemory.git

# Editable + test tooling
git clone https://github.com/mbgulden/swarmmemory.git
cd swarmmemory
pip install -e ".[test]"
```

*Pure Python standard library — zero runtime dependencies. Requires Python 3.9+.*

---

## 🚀 Quick Start

Under five minutes, end to end:

```python
import time
from pathlib import Path
from swarmmemory import (
    EpisodicStore, Episode, MemoryQuery,
    WorkingScratchpad, SemanticDistiller, MemoryIndex,
)

# 1. Episodic: remember what agents did
store = EpisodicStore("swarm.db")
store.store(Episode(
    episode_id="ep-001",
    agent_id="planner",
    event_type="decision",
    content="Chose SQLite for the prototype; revisit Postgres at 1M rows.",
    metadata={"task": "DB-12"},
    timestamp=time.time(),
    tags=["decision", "db"],
))
hits = store.recall(MemoryQuery(text="sqlite", tags=["decision"]))
print(hits[0].content)

# 2. Working: shared scratchpad with atomic compare-and-swap
scratch = WorkingScratchpad("swarm.db")
scratch.put("task/DB-12/owner", "planner", agent_id="planner")
entry = scratch.get("task/DB-12/owner")          # version == 1
ok = scratch.cas("task/DB-12/owner", entry.version, "builder", agent_id="builder")
print(ok)  # True — a stale writer with an old version gets False, not a clobber

# 3. Semantic: distill a codebase into token-capped context
distiller = SemanticDistiller()
nodes = distiller.distill_directory(Path("src"))
print(distiller.summarize_context(nodes, max_tokens=500))

# 4. Unified view
index = MemoryIndex(store, scratch)
print(index.stats())
print(index.export_context(MemoryQuery(text="sqlite"), max_tokens=200))
```

### CLI

```bash
# Recall episodes
swarmmemory query "sqlite" --db swarm.db

# Store health
swarmmemory stats --db swarm.db

# Garbage-collect episodes older than N days
swarmmemory gc --days 30 --db swarm.db

# Distill a file or directory of Python into semantic nodes
swarmmemory distill ./src
```

The default database is `memory.db` in the current directory; pass `--db :memory:` for a throwaway store.

---

## 🐍 API Reference

### `EpisodicStore` — append-only event log with full-text recall

```python
EpisodicStore(db_path: str = ":memory:")
store.store(episode: Episode) -> None            # raises MemoryError on duplicate id
store.recall(query: MemoryQuery) -> List[Episode] # FTS5 match + agent/tag filters, newest first
store.forget(episode_id: str) -> None
store.gc(max_age_days: int) -> int               # deletes old episodes, returns count
```

### `WorkingScratchpad` — versioned shared key-value store

```python
WorkingScratchpad(db_path: str = ":memory:")
pad.put(key, value, agent_id) -> None            # JSON-encodes value, bumps version
pad.get(key) -> Optional[WorkingEntry]           # key, value, owner_agent_id, created/updated_at, version
pad.cas(key, expected_version, new_value, agent_id) -> bool  # atomic compare-and-swap
pad.list_keys(prefix) -> List[str]
pad.clear(agent_id) -> int                       # deletes one agent's entries, returns count
```

### `SemanticDistiller` — AST-based code context

```python
SemanticDistiller()
distiller.distill_file(path: Path) -> List[SemanticNode]       # module/class/function nodes
distiller.distill_directory(path: Path) -> List[SemanticNode]  # recursive *.py
distiller.summarize_context(nodes, max_tokens=1000) -> str     # token-capped (~4 chars/token)
```

Each `SemanticNode` carries `symbol_name`, `symbol_type` (`module`/`class`/`function`), `file_path`, `line_range`, `docstring`, `dependencies` (base classes), and a one-line `summary`. Methods are namespaced as `ClassName.method`.

### `MemoryIndex` — unified search, stats, and export

```python
MemoryIndex(episodic_store, working_store)
index.search(query) -> List[Episode]                          # delegates to episodic recall
index.stats() -> MemoryStats                                  # totals for episodes + working entries
index.export_context(query, max_tokens=1000) -> str           # token-capped episode text
```

### Types

| Type | Fields |
|---|---|
| `Episode` | `episode_id`, `agent_id`, `event_type`, `content`, `metadata`, `timestamp`, `embedding` (optional), `tags` |
| `WorkingEntry` | `key`, `value`, `owner_agent_id`, `created_at`, `updated_at`, `version` |
| `SemanticNode` | `symbol_name`, `symbol_type`, `file_path`, `line_range`, `docstring`, `dependencies`, `summary` |
| `MemoryQuery` | `text`, `tags`, `agent_id`, `limit` (default 10) |
| `MemoryStats` | `total_episodes`, `total_working_entries`, `total_semantic_nodes`, `storage_bytes` |
| `MemoryError` | Base exception for all memory errors |

---

## ⚠️ What 0.1.0 honestly does (and doesn't)

- **Recall is keyword-based (FTS5), not vector similarity.** The `embedding` field on `Episode` is stored as JSON, but ranking in 0.1.0 comes from full-text match plus tag/agent filters — newest first.
- **Semantic nodes are distilled on demand, not persisted.** `stats().total_semantic_nodes` is `0` and `storage_bytes` is not computed in this release; run `distill` whenever you need fresh context.
- **One SQLite file per store.** Point both stores at the same file to keep a swarm's episodic + working memory together. `:memory:` gives a throwaway store that lives only for the process.

---

## 🤖 CI / CD Integration (GitHub Actions)

SwarmMemory ships with a CI workflow (3 OS × 4 Python) running the full test suite, `ruff` lint, CLI smoke tests, and a wheel/sdist build validated by `twine check`. Release artifacts publish via PyPI Trusted Publishing on GitHub Release.

---

## 🗺️ Swarm Ecosystem

SwarmMemory is part of the **Swarm Primitives Ecosystem** for autonomous agent swarms:

- 🔒 **SwarmLock**: Tokenized, non-blocking distributed advisory locks.
- ⏱️ **SwarmCron**: Native high-precision background cron scheduling.
- 🛡️ **SwarmProof**: Truth Oracle, evidence ledgers, and anti-hallucination gates.
- 🧠 **SwarmMemory**: Shared episodic, working, and semantic memory for agent swarms.
- 🔀 **SwarmRouter**: Intelligent query routing and model cascading *(coming soon)*.
- 🧭 **SwarmCurator**: Long-term memory distillation and context compaction *(coming soon)*.

Built to give Prismatic-engine swarms a shared, persistent memory layer: episodes to recall what happened, scratchpads to coordinate what's happening, distilled code context to act on.

---

## 📄 License
MIT © GrowthWebDev
