"""Adapters for Apify Actors that return public platform records."""

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.parse import quote

import requests

from collectors.base_collector import (
    BaseCollector,
    CollectorError,
    CollectorNotConfigured,
)
from models.post import SocialPost


class ApifyCollector(BaseCollector):
    actor_env: str
    target_kind: str

    def collect(self, query: str, limit: int | None) -> list[SocialPost]:
        token = os.getenv("APIFY_API_TOKEN")
        actor_id = os.getenv(self.actor_env)
        target = query.strip()
        if not token:
            raise CollectorNotConfigured("APIFY_API_TOKEN is not configured.")
        if not actor_id:
            raise CollectorNotConfigured(
                f"{self.actor_env} is not configured. Set it to an Apify Actor ID."
            )
        if not target:
            raise CollectorNotConfigured(
                f"No target configured for the {self.platform} scraper."
            )

        payload = _actor_input(self.platform, target, limit)
        custom_input = os.getenv(f"APIFY_INPUT_{self.platform.upper()}")
        if custom_input:
            try:
                payload = json.loads(custom_input)
            except json.JSONDecodeError as error:
                raise CollectorError(
                    f"APIFY_INPUT_{self.platform.upper()} must be valid JSON."
                ) from error

        normalized_actor_id = actor_id.replace("/", "~")
        endpoint = (
            "https://api.apify.com/v2/acts/"
            f"{quote(normalized_actor_id, safe='~')}/run-sync-get-dataset-items"
        )
        response: requests.Response | None = None
        last_error: requests.RequestException | None = None
        for attempt in range(3):
            try:
                response = requests.post(
                    endpoint,
                    params={"token": token, "format": "json", "clean": "true"},
                    json=payload,
                    timeout=(15, 180),
                )
                break
            except requests.RequestException as error:
                last_error = error
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
        if response is None:
            if last_error is None:
                raise CollectorError("Apify request failed without a response.")
            raise CollectorError(
                f"Apify request failed after 3 attempts: {last_error}"
            ) from last_error
        if not 200 <= response.status_code < 300:
            detail = response.text[:500].replace("\n", " ")
            raise CollectorError(
                f"Apify Actor {actor_id} failed with HTTP {response.status_code}: "
                f"{detail}"
            )
        try:
            raw = response.json()
        except ValueError as error:
            raise CollectorError("Apify returned an invalid JSON response.") from error
        return _normalize(self.platform, raw, target, limit)


class ApifyYouTubeCollector(ApifyCollector):
    platform = "youtube"
    actor_env = "APIFY_ACTOR_YOUTUBE"
    target_kind = "keyword"


class ApifyRedditCollector(ApifyCollector):
    platform = "reddit"
    actor_env = "APIFY_ACTOR_REDDIT"
    target_kind = "subreddit"


class ApifyInstagramCollector(ApifyCollector):
    platform = "instagram"
    actor_env = "APIFY_ACTOR_INSTAGRAM"
    target_kind = "username"


class ApifyFacebookCollector(ApifyCollector):
    platform = "facebook"
    actor_env = "APIFY_ACTOR_FACEBOOK"
    target_kind = "marketplace query"


class ApifyTikTokCollector(ApifyCollector):
    platform = "tiktok"
    actor_env = "APIFY_ACTOR_TIKTOK"
    target_kind = "keyword"


class ApifyXCollector(ApifyCollector):
    platform = "x"
    actor_env = "APIFY_ACTOR_X"
    target_kind = "profile or post URL"


class ApifyLinkedInCollector(ApifyCollector):
    platform = "linkedin"
    actor_env = "APIFY_ACTOR_LINKEDIN"
    target_kind = "public profile URL"


def _actor_input(platform: str, target: str, limit: int | None) -> dict[str, Any]:
    count = limit or 100
    if platform == "youtube":
        return {
            "searchQueries": [target],
            "maxResults": count,
            "maxResultsShorts": 0,
            "maxResultStreams": 0,
        }
    if platform == "reddit":
        return {"startUrls": [{"url": f"https://www.reddit.com/r/{target.removeprefix('r/')}"}], "maxItems": count}
    if platform == "instagram":
        return {"usernames": [target.removeprefix("@")], "resultsLimit": count}
    if platform == "tiktok":
        return {
            "hashtags": [target.removeprefix("#")],
            "resultsPerPage": count,
        }
    if platform == "x":
        return {"startUrls": [{"url": target}], "maxItems": count}
    if platform == "linkedin":
        return {"startUrls": [{"url": target}], "maxItems": count}
    if platform == "facebook":
        return {"searchQueries": [target], "maxItems": count}
    return {"searchQueries": [target], "maxItems": count}


def _normalize(
    platform: str, raw: Any, target: str, limit: int | None
) -> list[SocialPost]:
    records = raw if isinstance(raw, list) else (
        raw.get("data", []) if isinstance(raw, dict) else []
    )
    if not isinstance(records, list):
        records = [raw]
    posts: list[SocialPost] = []
    for index, record in enumerate(records[:limit] if limit else records, start=1):
        if not isinstance(record, dict):
            continue
        content = str(
            record.get("text") or record.get("description") or record.get("title")
            or record.get("caption") or record.get("content") or ""
        )
        url = str(
            record.get("url") or record.get("permalink") or record.get("postUrl")
            or record.get("webpageUrl") or record.get("videoUrl")
            or record.get("link") or ""
        )
        identifier = str(
            record.get("id") or record.get("videoId") or record.get("postId")
            or record.get("shortCode") or record.get("shortcode") or url
            or f"{platform}-{index}"
        )
        if platform == "youtube" and not url:
            youtube_id = record.get("videoId") or record.get("id")
            if youtube_id:
                url = f"https://www.youtube.com/watch?v={youtube_id}"
        posts.append(
            SocialPost(
                platform=platform,
                platform_post_id=identifier,
                author_name=str(
                    record.get("author") or record.get("username")
                    or record.get("ownerUsername") or record.get("channelName")
                    or target
                ),
                title=content[:120],
                content=content,
                url=url,
                likes_count=_integer(
                    record.get("likesCount") or record.get("likes")
                    or record.get("likeCount")
                ),
                comments_count=_integer(
                    record.get("commentsCount") or record.get("comments")
                ),
                views_count=_integer(
                    record.get("viewsCount") or record.get("views")
                    or record.get("viewCount")
                ),
                published_at=(
                    record.get("timestamp") or record.get("createdAt")
                    or record.get("publishedAt") or record.get("date")
                ),
            )
        )
    return posts


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
