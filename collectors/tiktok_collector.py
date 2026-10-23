"""TikTok Research API collector."""

from __future__ import annotations

import os

import requests

from collectors.base_collector import (
    BaseCollector,
    CollectorError,
    CollectorNotConfigured,
)
from models.post import SocialPost


class TikTokCollector(BaseCollector):
    platform = "tiktok"

    def collect(
        self, query: str, limit: int | None, use_demo_data: bool
    ) -> list[SocialPost]:
        access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
        if not access_token:
            raise CollectorNotConfigured("TIKTOK_ACCESS_TOKEN is not configured.")

        response = requests.post(
            "https://open.tiktokapis.com/v2/research/video/query/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "query": {
                    "and": [{"operation": "EQ", "field_name": "keyword", "field_values": [query]}]
                },
                "max_count": min(limit or 20, 100),
                "fields": [
                    "id", "video_description", "create_time", "like_count",
                    "comment_count", "share_count", "view_count", "username",
                ],
            },
            timeout=20,
        )
        if response.status_code != 200:
            raise CollectorError(
                f"TikTok request failed with HTTP {response.status_code}. "
                "Research API access must be approved for the app."
            )
        data = response.json().get("data", {}).get("videos", [])
        return [
            SocialPost(
                platform=self.platform,
                platform_post_id=item["id"],
                author_name=item.get("username", ""),
                title=item.get("video_description", "")[:120],
                content=item.get("video_description", ""),
                url=f"https://www.tiktok.com/@{item.get('username', '')}/video/{item['id']}",
                likes_count=item.get("like_count", 0),
                comments_count=item.get("comment_count", 0),
                views_count=item.get("view_count", 0),
                published_at=item.get("create_time"),
            )
            for item in data
        ]
