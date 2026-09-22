import sqlite3
import json
import time
import hashlib
from typing import Optional, Any
from .config import settings

class SQLiteCache:
    def __init__(self, db_path: str = settings.CACHE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_cache (
                    cache_key TEXT PRIMARY KEY,
                    method TEXT,
                    tool_name TEXT,
                    response_json TEXT,
                    created_at REAL
                )
            """)
            conn.commit()

    def _make_key(self, tool_name: str, arguments: dict) -> str:
        serialized = json.dumps({"tool": tool_name, "args": arguments}, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, tool_name: str, arguments: dict) -> Optional[Any]:
        key = self._make_key(tool_name, arguments)
        now = time.time()
        expire_before = now - (settings.CACHE_EXPIRE_HOURS * 3600)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT response_json, created_at FROM mcp_cache WHERE cache_key = ?", (key,))
            row = cursor.fetchone()
            if row:
                resp_str, created_at = row
                if created_at >= expire_before:
                    try:
                        return json.loads(resp_str)
                    except Exception:
                        pass
        return None

    def set(self, tool_name: str, arguments: dict, response_data: Any):
        key = self._make_key(tool_name, arguments)
        now = time.time()
        resp_str = json.dumps(response_data, ensure_ascii=False)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO mcp_cache (cache_key, method, tool_name, response_json, created_at)
                VALUES (?, 'tools/call', ?, ?, ?)
            """, (key, tool_name, resp_str, now))
            conn.commit()

cache = SQLiteCache()
