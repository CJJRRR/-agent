from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import IntelItem


class IntelStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.connection.close()

    def has_seen(self, content_hash: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM intel_items WHERE content_hash = ? LIMIT 1",
            (content_hash,),
        ).fetchone()
        return row is not None

    def save_item(self, item: IntelItem) -> None:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO intel_items (
                content_hash, competitor, source_name, source_type, source_url,
                title, url, content, published_at, fetched_at,
                category, impact, summary, business_implication
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.content_hash,
                item.competitor,
                item.source_name,
                item.source_type,
                item.source_url,
                item.title,
                item.url,
                item.content,
                item.published_at,
                item.fetched_at.isoformat(),
                item.category,
                item.impact,
                item.summary,
                item.business_implication,
            ),
        )
        self.connection.commit()

    def _init_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS intel_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT NOT NULL UNIQUE,
                competitor TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_url TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                content TEXT NOT NULL,
                published_at TEXT,
                fetched_at TEXT NOT NULL,
                category TEXT NOT NULL,
                impact TEXT NOT NULL,
                summary TEXT NOT NULL,
                business_implication TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_intel_competitor ON intel_items(competitor)"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_intel_impact ON intel_items(impact)"
        )
        self.connection.commit()
