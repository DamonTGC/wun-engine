"""cache.py

Simple SQLite-backed cache for Wun Engine.

Currently used to cache normalized props per sport so we don't hammer
The Odds API every request. This persists across restarts.
"""
from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Dict, List, Optional

from config import DB_PATH


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS props_cache (
            sport TEXT PRIMARY KEY,
            fetched_at REAL NOT NULL,
            data_json TEXT NOT NULL
        )
        """
    )
    return conn


def cache_props_for_sport(sport: str, props: List[Dict[str, Any]]) -> None:
    """Persist props for a sport as JSON payload.

    Props should already be JSON-serializable dictionaries (not dataclasses).
    """
    conn = _get_conn()
    try:
        payload = json.dumps(props)
        ts = time.time()
        conn.execute(
            "REPLACE INTO props_cache (sport, fetched_at, data_json) VALUES (?, ?, ?)",
            (sport.upper(), ts, payload),
        )
        conn.commit()
    finally:
        conn.close()


def get_cached_props_for_sport(
    sport: str, max_age_seconds: int
) -> Optional[List[Dict[str, Any]]]:
    """Return cached props for a sport if not older than max_age_seconds.

    Returns None if no usable cache is available.
    """
    conn = _get_conn()
    try:
        cur = conn.execute(
            "SELECT fetched_at, data_json FROM props_cache WHERE sport = ?",
            (sport.upper(),),
        )
        row = cur.fetchone()
        if not row:
            return None
        fetched_at, data_json = row
        age = time.time() - fetched_at
        if age > max_age_seconds:
            return None
        try:
            data = json.loads(data_json)
        except Exception:
            return None
        if not isinstance(data, list):
            return None
        return data
    finally:
        conn.close()
