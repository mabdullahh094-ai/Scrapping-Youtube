"""Parallel orchestration for all platform collectors."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from collectors.base_collector import BaseCollector
from collectors.meta_collector import FacebookCollector, InstagramCollector
from collectors.reddit_collector import RedditCollector
from collectors.tiktok_collector import TikTokCollector
from collectors.youtube_collector import YouTubeCollector
from collectors.x_collector import XCollector
from models.post import SocialPost


@dataclass(slots=True)
class CollectorResult:
    platform: str
    status: str
    posts: list[SocialPost] = field(default_factory=list)
    error: str | None = None


@dataclass(slots=True)
class CollectionReport:
    results: list[CollectorResult]

    @property
    def posts(self) -> list[SocialPost]:
        return [post for result in self.results for post in result.posts]


def run_all_collectors(
    query: str, limit: int | None, use_demo_data: bool
) -> CollectionReport:
    collectors: list[BaseCollector] = [
        YouTubeCollector(),
        RedditCollector(),
        XCollector(),
        InstagramCollector(),
        FacebookCollector(),
        TikTokCollector(),
    ]
    results: list[CollectorResult] = []
    with ThreadPoolExecutor(max_workers=len(collectors)) as executor:
        futures = {
            executor.submit(
                collector.collect, query, limit, use_demo_data
            ): collector.platform
            for collector in collectors
        }
        for future in as_completed(futures):
            platform = futures[future]
            try:
                results.append(
                    CollectorResult(
                        platform=platform,
                        status="success",
                        posts=future.result(),
                    )
                )
            except Exception as error:
                results.append(
                    CollectorResult(
                        platform=platform,
                        status="failed",
                        error=str(error),
                    )
                )
    return CollectionReport(sorted(results, key=lambda item: item.platform))
