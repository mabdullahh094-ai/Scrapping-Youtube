"""SQLite persistence for normalized records."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from models.post import SocialPost

DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "social_media.db"


def initialize_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                platform_post_id TEXT NOT NULL,
                author_name TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                url TEXT NOT NULL,
                likes_count INTEGER NOT NULL,
                comments_count INTEGER NOT NULL,
                views_count INTEGER NOT NULL,
                published_at TEXT,
                collected_at TEXT NOT NULL,
                UNIQUE(platform, platform_post_id)
            )
            """
        )


def save_posts(posts: list[SocialPost]) -> None:
    if not posts:
        return
    initialize_database()
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO posts (
                platform, platform_post_id, author_name, title, content, url,
                likes_count, comments_count, views_count, published_at, collected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    post.platform,
                    post.platform_post_id,
                    post.author_name,
                    post.title,
                    post.content,
                    post.url,
                    post.likes_count,
                    post.comments_count,
                    post.views_count,
                    post.published_at,
                    post.collected_at,
                )
                for post in posts
            ],
        )


def load_posts() -> list[SocialPost]:
    """Load all saved normalized records for local browsing/export."""
    initialize_database()
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT platform, platform_post_id, author_name, title, content, url,
                   likes_count, comments_count, views_count, published_at,
                   collected_at
            FROM posts
            ORDER BY collected_at DESC, id DESC
            """
        ).fetchall()
    return [SocialPost(*row) for row in rows]
