"""Adapters for the cloned ScrapFly public scraper examples."""

from __future__ import annotations

import asyncio
import importlib.util
import inspect
import os
from pathlib import Path
from typing import Any, Awaitable, Callable

from collectors.base_collector import (
    BaseCollector,
    CollectorError,
    CollectorNotConfigured,
)
from models.post import SocialPost


SCRAPERS_ROOT = Path(
    os.getenv(
        "SCRAPFLY_SCRAPERS_PATH",
        Path(__file__).resolve().parents[2] / "ScrapFly-Scrapers",
    )
)


class ScrapFlyCollector(BaseCollector):
    """Run one public ScrapFly example and normalize its output."""

    module_name: str
    entrypoint: str
    scraper_directory: str
    target_kind: str

    def collect(
        self, query: str, limit: int | None, use_demo_data: bool
    ) -> list[SocialPost]:
        if not os.getenv("SCRAPFLY_KEY"):
            raise CollectorNotConfigured("SCRAPFLY_KEY is not configured.")
        target = query.strip()
        if not target:
            raise CollectorNotConfigured(
                f"No target configured for the {self.platform} scraper."
            )
        module = _load_module(self.module_name, self.platform)
        operation = self._operation(module, target, limit)
        try:
            raw = asyncio.run(_consume(operation))
        except ValueError as error:
            if "Expecting value" in str(error):
                raise CollectorError(
                    f"{self.platform} returned an invalid/empty response. "
                    "Retry the scrape or use a different public target."
                ) from error
            raise
        return _normalize(self.platform, raw, target, limit)

    def _operation(
        self, module: Any, target: str, limit: int | None
    ) -> Callable[[], Any]:
        raise NotImplementedError


class ScrapFlyYouTubeCollector(ScrapFlyCollector):
    platform = "youtube"
    module_name = "youtube"
    entrypoint = "youtube.py"
    scraper_directory = "youtube-scraper"
    target_kind = "keyword"

    def _operation(self, module: Any, target: str, limit: int | None) -> Callable[[], Awaitable[Any]]:
        return lambda: module.scrape_search(
            search_query=target,
            max_scrape_pages=max(1, min(limit or 1, 3)),
        )


class ScrapFlyRedditCollector(ScrapFlyCollector):
    platform = "reddit"
    module_name = "reddit"
    entrypoint = "reddit.py"
    scraper_directory = "reddit-scraper"
    target_kind = "subreddit"

    def _operation(self, module: Any, target: str, limit: int | None) -> Callable[[], Awaitable[Any]]:
        return lambda: module.scrape_subreddit(
            subreddit_id=target.removeprefix("r/"),
            max_pages=max(1, min(limit or 1, 3)),
        )


class ScrapFlyInstagramCollector(ScrapFlyCollector):
    platform = "instagram"
    module_name = "instagram"
    entrypoint = "instagram.py"
    scraper_directory = "instagram-scraper"
    target_kind = "username"

    def _operation(self, module: Any, target: str, limit: int | None) -> Callable[[], Awaitable[Any]]:
        return lambda: module.scrape_user_posts(
            username=target.removeprefix("@"),
            page_size=min(limit or 12, 50),
            max_pages=max(1, min(limit or 1, 3)),
        )


class ScrapFlyFacebookCollector(ScrapFlyCollector):
    platform = "facebook"
    module_name = "facebook"
    entrypoint = "facebook.py"
    scraper_directory = "facebook-scraper"
    target_kind = "marketplace query"

    def _operation(self, module: Any, target: str, limit: int | None) -> Callable[[], Awaitable[Any]]:
        return lambda: module.scrape_marketplace_listings(query=target)


class ScrapFlyTikTokCollector(ScrapFlyCollector):
    platform = "tiktok"
    module_name = "tiktok"
    entrypoint = "tiktok.py"
    scraper_directory = "tiktok-scraper"
    target_kind = "keyword"

    def _operation(self, module: Any, target: str, limit: int | None) -> Callable[[], Awaitable[Any]]:
        return lambda: module.scrape_search(keyword=target)


class ScrapFlyXCollector(ScrapFlyCollector):
    platform = "x"
    module_name = "twitter"
    entrypoint = "twitter.py"
    scraper_directory = "twitter-scraper"
    target_kind = "profile or post URL"

    def _operation(self, module: Any, target: str, limit: int | None) -> Callable[[], Awaitable[Any]]:
        if "/status/" in target:
            return lambda: module.scrape_tweet(url=target)
        return lambda: module.scrape_profile(url=target)


def _load_module(module_name: str, platform: str) -> Any:
    directory = {
        "x": "twitter-scraper",
    }.get(platform, f"{platform}-scraper")
    path = SCRAPERS_ROOT / directory / f"{module_name}.py"
    if not path.is_file():
        raise FileNotFoundError(
            f"ScrapFly {platform} scraper not found at {path}. "
            "Set SCRAPFLY_SCRAPERS_PATH to the cloned repository."
        )
    spec = importlib.util.spec_from_file_location(f"scrapfly_{module_name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load ScrapFly {platform} scraper module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize(
    platform: str, raw: Any, target: str, limit: int | None
) -> list[SocialPost]:
    records = _records(raw)
    if limit is not None:
        records = records[:limit]
    posts: list[SocialPost] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            continue
        identifier = str(
            record.get("id")
            or record.get("videoId")
            or record.get("shortcode")
            or record.get("url")
            or f"{platform}-{index}"
        )
        content = str(
            record.get("text")
            or record.get("description")
            or record.get("title")
            or record.get("caption")
            or ""
        )
        url = str(record.get("url") or record.get("permalink") or "")
        posts.append(
            SocialPost(
                platform=platform,
                platform_post_id=identifier,
                author_name=str(
                    record.get("author")
                    or record.get("username")
                    or record.get("channel")
                    or target
                ),
                title=content[:120],
                content=content,
                url=url,
                likes_count=_integer(record.get("likes") or record.get("like_count")),
                comments_count=_integer(
                    record.get("comments") or record.get("comment_count")
                ),
                views_count=_integer(record.get("views") or record.get("view_count")),
                published_at=record.get("created_at") or record.get("published_at"),
            )
        )
    return posts


def _records(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        if isinstance(value.get("post_data"), list):
            return value["post_data"]
        for key in ("videos", "posts", "items", "results", "data", "tweets"):
            if isinstance(value.get(key), list):
                return value[key]
        return [value]
    return []


async def _consume(operation: Callable[[], Any]) -> Any:
    result = operation()
    if inspect.isasyncgen(result):
        return [item async for item in result]
    if inspect.isawaitable(result):
        return await result
    raise TypeError(f"ScrapFly operation returned unsupported value: {type(result)!r}")


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
