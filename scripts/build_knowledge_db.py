#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from outbush_ai.content import KNOWLEDGE_ITEMS, Source

DB_PATH = ROOT / "data" / "outbush_knowledge.sqlite"


def source_key(source: Source) -> str:
    return source.url


def main() -> int:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = DB_PATH.with_suffix(".sqlite.tmp")
    if tmp_path.exists():
        tmp_path.unlink()
    conn = sqlite3.connect(tmp_path)
    try:
        conn.executescript(
            """
            PRAGMA journal_mode = DELETE;
            PRAGMA foreign_keys = ON;

            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE sources (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                retrieved TEXT NOT NULL,
                jurisdiction TEXT NOT NULL,
                category TEXT NOT NULL
            );

            CREATE TABLE knowledge_items (
                key TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                text TEXT NOT NULL,
                source_id INTEGER NOT NULL REFERENCES sources(id),
                tags_json TEXT NOT NULL,
                risk TEXT NOT NULL,
                sort_order INTEGER NOT NULL
            );

            CREATE VIRTUAL TABLE knowledge_fts USING fts5(
                key UNINDEXED,
                title,
                text,
                tags
            );
            """
        )
        conn.executemany(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            [
                ("format", "outbush-knowledge-v1"),
                ("item_count", str(len(KNOWLEDGE_ITEMS))),
                ("generated_from", "outbush_ai.content.KNOWLEDGE_ITEMS"),
            ],
        )
        source_ids: dict[str, int] = {}
        for item in KNOWLEDGE_ITEMS:
            key = source_key(item.source)
            if key in source_ids:
                continue
            cursor = conn.execute(
                """
                INSERT INTO sources(title, url, retrieved, jurisdiction, category)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item.source.title,
                    item.source.url,
                    item.source.retrieved,
                    item.source.jurisdiction,
                    item.source.category,
                ),
            )
            source_ids[key] = int(cursor.lastrowid)
        for order, item in enumerate(KNOWLEDGE_ITEMS):
            conn.execute(
                """
                INSERT INTO knowledge_items(key, title, text, source_id, tags_json, risk, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.key,
                    item.title,
                    item.text,
                    source_ids[source_key(item.source)],
                    json.dumps(item.tags),
                    item.risk,
                    order,
                ),
            )
            conn.execute(
                """
                INSERT INTO knowledge_fts(key, title, text, tags)
                VALUES (?, ?, ?, ?)
                """,
                (item.key, item.title, item.text, " ".join(item.tags)),
            )
        conn.commit()
    finally:
        conn.close()
    tmp_path.replace(DB_PATH)
    print(f"Wrote {DB_PATH} with {len(KNOWLEDGE_ITEMS)} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
