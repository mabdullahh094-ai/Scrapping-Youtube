"""Reddit collector using the official OAuth API."""

from __future__ import annotations

import os

import requests

from collectors.base_collector import BaseCollector, CollectorError
from models.post import SocialPost


class RedditCollector(BaseCollector):
    platform = "reddit"

    def collect(
        self, query: str, limit: int | None, use_demo_data: bool
    ) -> list[SocialPost]:
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise CollectorError(
                "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are not configured."
            )

        token_response = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": os.getenv("REDDIT_USER_AGENT", "social-collector/1.0")},
            timeout=20,
        )
        if token_response.status_code != 200:
            raise CollectorError(
                f"Reddit token request failed with HTTP {token_response.status_code}."
            )
        token = token_response.json().get("access_token")
        if not token:
            raise CollectorError("Reddit token response did not include an access token.")

        page_size = min(limit or 25, 100)
        response = requests.get(
            "https://oauth.reddit.com/search.json",
            params={"q": query, "limit": page_size, "sort": "relevance"},
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": os.getenv("REDDIT_USER_AGENT", "social-collector/1.0"),
            },
            timeout=20,
        )
        if response.status_code != 200:
            raise CollectorError(
                f"Reddit search request failed with HTTP {response.status_code}."
            )

        children = response.json().get("data", {}).get("children", [])
        return [
            SocialPost(
                platform=self.platform,
                platform_post_id=item["data"]["name"],
                author_name=item["data"].get("author") or "[deleted]",
                title=item["data"].get("title", ""),
                content=item["data"].get("selftext", ""),
                url=f"https://www.reddit.com{item['data'].get('permalink', '')}",
                likes_count=item["data"].get("score", 0),
                comments_count=item["data"].get("num_comments", 0),
                published_at=None,
            )
            for item in children
        ]
