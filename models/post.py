"""Normalized social-media post model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class SocialPost:
    platform: str
    platform_post_id: str
    author_name: str
    title: str
    content: str
    url: str
    likes_count: int = 0
    comments_count: int = 0
    views_count: int = 0
    published_at: str | None = None
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
