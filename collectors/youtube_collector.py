"""YouTube Data API collector."""

from __future__ import annotations

import os

import requests

from collectors.base_collector import BaseCollector, CollectorError
from models.post import SocialPost


class YouTubeCollector(BaseCollector):
    platform = "youtube"
    endpoint = "https://www.googleapis.com/youtube/v3/search"

    def collect(self, query: str, limit: int, use_demo_data: bool) -> list[SocialPost]:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            if use_demo_data:
                return self.demo_posts(query, limit)
            raise CollectorError("YOUTUBE_API_KEY is not configured.")

        response = requests.get(
            self.endpoint,
            params={
                "key": api_key,
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": limit,
            },
            timeout=20,
        )
        if response.status_code != 200:
            raise CollectorError(
                f"YouTube API request failed with HTTP {response.status_code}. "
                "Check that the key is active and YouTube Data API v3 is enabled."
            )
        items = response.json().get("items", [])
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
