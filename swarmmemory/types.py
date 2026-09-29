from __future__ import annotations

import dataclasses
from typing import Any


class MemoryError(Exception):
    """Base exception for all Memory errors."""

@dataclasses.dataclass
class Episode:
    episode_id: str
    agent_id: str
    event_type: str
    content: str
    metadata: dict[str, Any]
    timestamp: float
    embedding: list[float] | None = None
    tags: list[str] = dataclasses.field(default_factory=list)

@dataclasses.dataclass
class WorkingEntry:
    key: str
    value: Any
    owner_agent_id: str
    created_at: float
    updated_at: float
    version: int

@dataclasses.dataclass
class SemanticNode:
    symbol_name: str
    symbol_type: str
    file_path: str
    line_range: tuple[int, int]
    docstring: str
    dependencies: list[str]
    summary: str

@dataclasses.dataclass
class MemoryQuery:
    text: str
    tags: list[str] = dataclasses.field(default_factory=list)
    agent_id: str | None = None
    limit: int = 10
    min_relevance: float = 0.0

@dataclasses.dataclass
class MemoryStats:
    total_episodes: int
    total_working_entries: int
    total_semantic_nodes: int
    storage_bytes: int
