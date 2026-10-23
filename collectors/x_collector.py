"""X collector using the official API v2."""

from __future__ import annotations

import os

import requests

from collectors.base_collector import BaseCollector, CollectorError
from models.post import SocialPost


class XCollector(BaseCollector):
    platform = "x"

    def collect(
        self, query: str, limit: int | None, use_demo_data: bool
    ) -> list[SocialPost]:
        bearer_token = os.getenv("X_BEARER_TOKEN")
        if not bearer_token:
            raise CollectorError("X_BEARER_TOKEN is not configured.")

        response = requests.get(
            "https://api.x.com/2/tweets/search/recent",
            params={
                "query": query,
                "max_results": max(10, min(limit or 10, 100)),
                "tweet.fields": "author_id,created_at,public_metrics",
                "expansions": "author_id",
                "user.fields": "name,username",
            },
            headers={"Authorization": f"Bearer {bearer_token}"},
            timeout=20,
        )
        if response.status_code != 200:
            raise CollectorError(
                f"X search request failed with HTTP {response.status_code}."
            )

        payload = response.json()
        users = {
            user["id"]: user for user in payload.get("includes", {}).get("users", [])
        }
        return [
            self._to_post(tweet, users.get(tweet.get("author_id")))
            for tweet in payload.get("data", [])
        ]

    def _to_post(self, tweet: dict, user: dict | None) -> SocialPost:
        metrics = tweet.get("public_metrics", {})
        username = (user or {}).get("username", "")
        return SocialPost(
            platform=self.platform,
            platform_post_id=tweet["id"],
            author_name=(user or {}).get("name", username),
            title=tweet.get("text", "")[:120],
            content=tweet.get("text", ""),
            url=f"https://x.com/{username}/status/{tweet['id']}" if username else "",
            likes_count=metrics.get("like_count", 0),
            comments_count=metrics.get("reply_count", 0),
            views_count=metrics.get("impression_count", 0),
            published_at=tweet.get("created_at"),
        )
