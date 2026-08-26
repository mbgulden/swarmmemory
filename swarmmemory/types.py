import dataclasses
from typing import Any, Dict, List, Optional, Tuple

class MemoryError(Exception):
    """Base exception for all Memory errors."""
    pass

@dataclasses.dataclass
class Episode:
    episode_id: str
    agent_id: str
    event_type: str
    content: str
    metadata: Dict[str, Any]
    timestamp: float
    embedding: Optional[List[float]] = None
    tags: List[str] = dataclasses.field(default_factory=list)

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
    line_range: Tuple[int, int]
    docstring: str
    dependencies: List[str]
    summary: str

@dataclasses.dataclass
class MemoryQuery:
    text: str
    tags: List[str] = dataclasses.field(default_factory=list)
    agent_id: Optional[str] = None
    limit: int = 10
    min_relevance: float = 0.0

@dataclasses.dataclass
class MemoryStats:
    total_episodes: int
    total_working_entries: int
    total_semantic_nodes: int
    storage_bytes: int
