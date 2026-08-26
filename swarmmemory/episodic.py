import sqlite3
import json
import time
from typing import List, Optional
from pathlib import Path
from .types import Episode, MemoryQuery, MemoryError

class EpisodicStore:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = f"file:memdb_{id(self)}?mode=memory&cache=shared" if db_path == ":memory:" else db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path, uri=True) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    event_type TEXT,
                    content TEXT,
                    metadata TEXT,
                    timestamp REAL,
                    embedding TEXT,
                    tags TEXT
                )
            ''')
            conn.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(
                    content,
                    content="episodes",
                    content_rowid="rowid"
                )
            ''')
            # Trigger to update fts table
            conn.execute('''
                CREATE TRIGGER IF NOT EXISTS episodes_ai AFTER INSERT ON episodes BEGIN
                    INSERT INTO episodes_fts(rowid, content) VALUES (new.rowid, new.content);
                END;
            ''')
            conn.execute('''
                CREATE TRIGGER IF NOT EXISTS episodes_ad AFTER DELETE ON episodes BEGIN
                    INSERT INTO episodes_fts(episodes_fts, rowid, content) VALUES ('delete', old.rowid, old.content);
                END;
            ''')

    def store(self, episode: Episode) -> None:
        try:
            with sqlite3.connect(self.db_path, uri=True) as conn:
                conn.execute('''
                    INSERT INTO episodes (episode_id, agent_id, event_type, content, metadata, timestamp, embedding, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    episode.episode_id,
                    episode.agent_id,
                    episode.event_type,
                    episode.content,
                    json.dumps(episode.metadata),
                    episode.timestamp,
                    json.dumps(episode.embedding) if episode.embedding else None,
                    json.dumps(episode.tags)
                ))
        except sqlite3.IntegrityError as e:
            raise MemoryError(f"Failed to store episode: {e}")

    def recall(self, query: MemoryQuery) -> List[Episode]:
        # For this implementation, we do a basic FTS search combined with standard queries
        with sqlite3.connect(self.db_path, uri=True) as conn:
            sql = "SELECT e.episode_id, e.agent_id, e.event_type, e.content, e.metadata, e.timestamp, e.embedding, e.tags FROM episodes e"
            params = []
            
            conditions = []
            
            if query.text:
                conditions.append("e.rowid IN (SELECT rowid FROM episodes_fts WHERE content MATCH ?)")
                params.append(query.text)
                
            if query.agent_id:
                conditions.append("e.agent_id = ?")
                params.append(query.agent_id)
                
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
                
            sql += " ORDER BY e.timestamp DESC LIMIT ?"
            params.append(query.limit)
            
            cursor = conn.execute(sql, params)
            results = []
            for row in cursor.fetchall():
                tags = json.loads(row[7]) if row[7] else []
                # Simple tag filter if tags were provided
                if query.tags and not all(tag in tags for tag in query.tags):
                    continue
                    
                results.append(Episode(
                    episode_id=row[0],
                    agent_id=row[1],
                    event_type=row[2],
                    content=row[3],
                    metadata=json.loads(row[4]) if row[4] else {},
                    timestamp=row[5],
                    embedding=json.loads(row[6]) if row[6] else None,
                    tags=tags
                ))
            return results

    def forget(self, episode_id: str) -> None:
        with sqlite3.connect(self.db_path, uri=True) as conn:
            conn.execute("DELETE FROM episodes WHERE episode_id = ?", (episode_id,))

    def gc(self, max_age_days: int) -> int:
        cutoff = time.time() - (max_age_days * 24 * 60 * 60)
        with sqlite3.connect(self.db_path, uri=True) as conn:
            cursor = conn.execute("DELETE FROM episodes WHERE timestamp < ?", (cutoff,))
            return cursor.rowcount
