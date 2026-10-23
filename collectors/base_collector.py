"""Shared collector contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.post import SocialPost


class CollectorError(Exception):
    """Expected error raised when a platform cannot be collected."""


class CollectorNotConfigured(CollectorError):
    """Raised when a platform's required API credentials are missing."""


class CollectorBlocked(CollectorError):
    """Raised when the upstream provider blocks a public scrape."""


class BaseCollector(ABC):
    platform: str

    @abstractmethod
    def collect(
        self, query: str, limit: int | None
    ) -> list[SocialPost]:
        """Collect public records for a query."""
