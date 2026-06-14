from __future__ import annotations

import json
from pathlib import Path
import re
import sqlite3
from functools import lru_cache
from typing import Iterable

from .content import KNOWLEDGE_ITEMS, KnowledgeItem, Source


WORD_RE = re.compile(r"[a-z0-9]+")
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "outbush_knowledge.sqlite"
STOP_WORDS = {
    "about",
    "australia",
    "australian",
    "before",
    "blue",
    "check",
    "day",
    "general",
    "should",
    "what",
    "with",
}


def _tokens(text: str) -> set[str]:
    return set(WORD_RE.findall(text.lower()))


class KnowledgeIndex:
    def __init__(self, items: Iterable[KnowledgeItem] | None = None, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.backend = "memory"
        self.items = list(items) if items is not None else []
        self._conn = sqlite3.connect(":memory:")
        self._fts_enabled = True
        if items is None and db_path.exists():
            try:
                self._conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                self.items = self._load_items_from_db()
                self.backend = "sqlite"
                self._by_key = {item.key: item for item in self.items}
                return
            except sqlite3.Error:
                self._conn = sqlite3.connect(":memory:")
                self.items = list(KNOWLEDGE_ITEMS)
                self.backend = "memory_fallback"
        elif not self.items:
            self.items = list(KNOWLEDGE_ITEMS)
        try:
            self._conn.execute(
                "CREATE VIRTUAL TABLE knowledge_fts USING fts5(key, title, text, tags)"
            )
            self._conn.executemany(
                "INSERT INTO knowledge_fts(key, title, text, tags) VALUES (?, ?, ?, ?)",
                [
                    (item.key, item.title, item.text, " ".join(item.tags))
                    for item in self.items
                ],
            )
            self._conn.commit()
        except sqlite3.Error:
            self._fts_enabled = False
        self._by_key = {item.key: item for item in self.items}

    def summary(self) -> dict:
        return {
            "backend": self.backend,
            "db_path": str(self.db_path),
            "items": len(self.items),
            "fts_enabled": self._fts_enabled,
        }

    def search(self, query: str, limit: int = 4) -> list[KnowledgeItem]:
        query = query.strip()
        if not query:
            return list(self.items[:limit])
        if self._fts_enabled:
            matches = self._search_fts(query, limit)
            if matches:
                return matches
        return self._search_keywords(query, limit)

    def _search_fts(self, query: str, limit: int) -> list[KnowledgeItem]:
        words = [
            word
            for word in WORD_RE.findall(query.lower())
            if len(word) > 2 and word not in STOP_WORDS
        ]
        if not words:
            return []
        fts_query = " OR ".join(words[:8])
        try:
            rows = self._conn.execute(
                """
                SELECT key
                FROM knowledge_fts
                WHERE knowledge_fts MATCH ?
                ORDER BY bm25(knowledge_fts)
                LIMIT ?
                """,
                (fts_query, limit),
            ).fetchall()
        except sqlite3.Error:
            return []
        return [self._by_key[row[0]] for row in rows if row[0] in self._by_key]

    def _search_keywords(self, query: str, limit: int) -> list[KnowledgeItem]:
        q = _tokens(query)
        scored: list[tuple[int, KnowledgeItem]] = []
        for item in self.items:
            body = _tokens(" ".join((item.title, item.text, " ".join(item.tags))))
            score = len(q & body)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def _load_items_from_db(self) -> list[KnowledgeItem]:
        rows = self._conn.execute(
            """
            SELECT
                k.key,
                k.title,
                k.text,
                k.tags_json,
                k.risk,
                s.title,
                s.url,
                s.retrieved,
                s.jurisdiction,
                s.category
            FROM knowledge_items k
            JOIN sources s ON s.id = k.source_id
            ORDER BY k.sort_order, k.key
            """
        ).fetchall()
        items: list[KnowledgeItem] = []
        for row in rows:
            source = Source(
                title=row[5],
                url=row[6],
                retrieved=row[7],
                jurisdiction=row[8],
                category=row[9],
            )
            tags = tuple(json.loads(row[3]))
            items.append(
                KnowledgeItem(
                    key=row[0],
                    title=row[1],
                    text=row[2],
                    source=source,
                    tags=tags,
                    risk=row[4],
                )
            )
        # Validate the FTS table before trusting the DB.
        self._conn.execute("SELECT key FROM knowledge_fts LIMIT 1").fetchall()
        return items


@lru_cache(maxsize=1)
def get_index() -> KnowledgeIndex:
    return KnowledgeIndex()
