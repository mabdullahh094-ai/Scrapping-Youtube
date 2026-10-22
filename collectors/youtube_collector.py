"""YouTube Data API collector."""

from __future__ import annotations

import os

import requests

from collectors.base_collector import BaseCollector, CollectorError
from models.post import SocialPost


class YouTubeCollector(BaseCollector):
    platform = "youtube"
    endpoint = "https://www.googleapis.com/youtube/v3/search"

    def collect(
        self, query: str, limit: int | None, use_demo_data: bool
    ) -> list[SocialPost]:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            if use_demo_data:
                return self.demo_posts(query, limit)
            raise CollectorError("YOUTUBE_API_KEY is not configured.")

        items: list[dict] = []
        page_token: str | None = None
        while limit is None or len(items) < limit:
            page_size = 50 if limit is None else min(50, limit - len(items))
            params = {
                "key": api_key,
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": page_size,
            }
            if page_token:
                params["pageToken"] = page_token
            response = requests.get(self.endpoint, params=params, timeout=20)
            if response.status_code != 200:
                raise CollectorError(
                    f"YouTube API request failed with HTTP {response.status_code}. "
                    "Check that the key is active and YouTube Data API v3 is enabled."
                )
            payload = response.json()
            items.extend(payload.get("items", []))
            page_token = payload.get("nextPageToken")
            if not page_token:
                break

        return [
            SocialPost(
                platform=self.platform,
                platform_post_id=item["id"]["videoId"],
                author_name=item["snippet"].get("channelTitle", ""),
                title=item["snippet"].get("title", ""),
                content=item["snippet"].get("description", ""),
                url=f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                published_at=item["snippet"].get("publishedAt"),
            )
            for item in items
        ]
