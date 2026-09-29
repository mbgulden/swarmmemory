from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

from .types import WorkingEntry


class WorkingScratchpad:
    def __init__(self, db_path: str = ":memory:"):
        if db_path == ":memory:":
            # Shared-cache in-memory DBs are destroyed when the last connection
            # closes, so hold one connection open for the store's lifetime.
            self.db_path = f"file:memdb_{id(self)}?mode=memory&cache=shared"
            self._keepalive = sqlite3.connect(self.db_path, uri=True)
        else:
            self.db_path = db_path
            self._keepalive = None
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path, uri=True) as conn:
            # enable WAL
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute('''
                CREATE TABLE IF NOT EXISTS working (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    owner_agent_id TEXT,
                    created_at REAL,
                    updated_at REAL,
                    version INTEGER
                )
            ''')

    def put(self, key: str, value: Any, agent_id: str) -> None:
        with sqlite3.connect(self.db_path, uri=True) as conn:
            cursor = conn.execute("SELECT version FROM working WHERE key = ?", (key,))
            row = cursor.fetchone()

            now = time.time()
            if row:
                version = row[0] + 1
                conn.execute('''
                    UPDATE working
                    SET value = ?, owner_agent_id = ?, updated_at = ?, version = ?
                    WHERE key = ?
                ''', (json.dumps(value), agent_id, now, version, key))
            else:
                conn.execute('''
                    INSERT INTO working (key, value, owner_agent_id, created_at, updated_at, version)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (key, json.dumps(value), agent_id, now, now, 1))

    def get(self, key: str) -> WorkingEntry | None:
        with sqlite3.connect(self.db_path, uri=True) as conn:
            cursor = conn.execute('''
                SELECT key, value, owner_agent_id, created_at, updated_at, version
                FROM working WHERE key = ?
            ''', (key,))
            row = cursor.fetchone()
            if not row:
                return None

            return WorkingEntry(
                key=row[0],
                value=json.loads(row[1]),
                owner_agent_id=row[2],
                created_at=row[3],
                updated_at=row[4],
                version=row[5]
            )

    def cas(self, key: str, expected_version: int, new_value: Any, agent_id: str) -> bool:
        with sqlite3.connect(self.db_path, uri=True) as conn:
            cursor = conn.execute("SELECT version FROM working WHERE key = ?", (key,))
            row = cursor.fetchone()

            if not row:
                return False

            current_version = row[0]
            if current_version != expected_version:
                return False

            now = time.time()
            conn.execute('''
                UPDATE working
                SET value = ?, owner_agent_id = ?, updated_at = ?, version = ?
                WHERE key = ? AND version = ?
            ''', (json.dumps(new_value), agent_id, now, current_version + 1, key, expected_version))
            return True

    def list_keys(self, prefix: str) -> list[str]:
        with sqlite3.connect(self.db_path, uri=True) as conn:
            cursor = conn.execute("SELECT key FROM working WHERE key LIKE ?", (f"{prefix}%",))
            return [row[0] for row in cursor.fetchall()]

    def clear(self, agent_id: str) -> int:
        with sqlite3.connect(self.db_path, uri=True) as conn:
            cursor = conn.execute("DELETE FROM working WHERE owner_agent_id = ?", (agent_id,))
            return cursor.rowcount
