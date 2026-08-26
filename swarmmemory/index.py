import sqlite3
from typing import List, Union
from .types import MemoryQuery, MemoryStats, Episode, SemanticNode
from .episodic import EpisodicStore
from .working import WorkingScratchpad

class MemoryIndex:
    def __init__(self, episodic_store: EpisodicStore, working_store: WorkingScratchpad):
        self.episodic = episodic_store
        self.working = working_store

    def search(self, query: MemoryQuery) -> List[Union[Episode, SemanticNode]]:
        # In a real implementation, this would query a unified vector index.
        # Here we just delegate to episodic store as semantic store is AST-based and doesn't store to DB currently.
        results: List[Union[Episode, SemanticNode]] = []
        episodes = self.episodic.recall(query)
        results.extend(episodes)
        return results

    def stats(self) -> MemoryStats:
        total_episodes = 0
        with sqlite3.connect(self.episodic.db_path, uri=True) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM episodes")
            total_episodes = cur.fetchone()[0]

        total_working = 0
        with sqlite3.connect(self.working.db_path, uri=True) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM working")
            total_working = cur.fetchone()[0]

        # Semantic nodes are not persistently stored in this implementation
        total_semantic = 0
        
        return MemoryStats(
            total_episodes=total_episodes,
            total_working_entries=total_working,
            total_semantic_nodes=total_semantic,
            storage_bytes=0 # Approximation omitted for simplicity
        )

    def export_context(self, query: MemoryQuery, max_tokens: int = 1000) -> str:
        results = self.episodic.recall(query)
        max_chars = max_tokens * 4
        
        lines = []
        current_chars = 0
        
        for ep in results:
            entry = f"[{ep.timestamp}] {ep.agent_id} ({ep.event_type}): {ep.content}"
            if current_chars + len(entry) > max_chars:
                lines.append("... (truncated)")
                break
            lines.append(entry)
            current_chars += len(entry)
            
        return "\n".join(lines)
