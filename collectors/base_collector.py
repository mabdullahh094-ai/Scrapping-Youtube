"""Shared collector contract and demo records."""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.post import SocialPost


class CollectorError(Exception):
    """Expected error raised when a platform cannot be collected."""


class BaseCollector(ABC):
    platform: str

    @abstractmethod
    def collect(
        self, query: str, limit: int | None, use_demo_data: bool
    ) -> list[SocialPost]:
        """Collect public records for a query."""

    def demo_posts(self, query: str, limit: int) -> list[SocialPost]:
        return [
            SocialPost(
                platform=self.platform,
                platform_post_id=f"demo-{index}",
                author_name=f"{self.platform.title()} demo account",
                title=f"{query} result {index}",
                content=f"Demo record for {query}. Connect the official API for live data.",
                url="https://example.com",
                likes_count=index * 10,
                comments_count=index,
                views_count=index * 100,
            )
            for index in range(1, limit + 1)
        ]
