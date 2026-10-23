"""Facebook Page and Instagram Business collectors through Meta Graph API."""

from __future__ import annotations

import os

import requests

from collectors.base_collector import BaseCollector, CollectorError
from models.post import SocialPost


class FacebookCollector(BaseCollector):
    platform = "facebook"

    def collect(
        self, query: str, limit: int | None, use_demo_data: bool
    ) -> list[SocialPost]:
        page_id = os.getenv("FACEBOOK_PAGE_ID")
        access_token = os.getenv("META_ACCESS_TOKEN")
        if not page_id or not access_token:
            raise CollectorError(
                "FACEBOOK_PAGE_ID and META_ACCESS_TOKEN are not configured."
            )
        data = _get_graph_feed(page_id, access_token, limit)
        return [
            _meta_post(self.platform, item, f"https://www.facebook.com/{page_id}")
            for item in data
            if query.lower() in item.get("message", "").lower()
            or not query.strip()
        ]


class InstagramCollector(BaseCollector):
    platform = "instagram"

    def collect(
        self, query: str, limit: int | None, use_demo_data: bool
    ) -> list[SocialPost]:
        account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        access_token = os.getenv("META_ACCESS_TOKEN")
        if not account_id or not access_token:
            raise CollectorError(
                "INSTAGRAM_BUSINESS_ACCOUNT_ID and META_ACCESS_TOKEN are not configured."
            )
        response = requests.get(
            f"https://graph.facebook.com/v21.0/{account_id}/media",
            params={
                "access_token": access_token,
                "fields": "id,caption,media_type,permalink,timestamp,like_count,comments_count",
                "limit": min(limit or 25, 100),
            },
            timeout=20,
        )
        if response.status_code != 200:
            raise CollectorError(
                f"Instagram request failed with HTTP {response.status_code}."
            )
        data = response.json().get("data", [])
        return [
            _meta_post(self.platform, item, item.get("permalink", ""))
            for item in data
            if query.lower() in item.get("caption", "").lower() or not query.strip()
        ]


def _get_graph_feed(page_id: str, access_token: str, limit: int | None) -> list[dict]:
    response = requests.get(
        f"https://graph.facebook.com/v21.0/{page_id}/feed",
        params={
            "access_token": access_token,
            "fields": "id,message,permalink_url,created_time,likes.summary(true),comments.summary(true)",
            "limit": min(limit or 25, 100),
        },
        timeout=20,
    )
    if response.status_code != 200:
        raise CollectorError(
            f"Facebook request failed with HTTP {response.status_code}."
        )
    return response.json().get("data", [])


def _meta_post(platform: str, item: dict, fallback_url: str) -> SocialPost:
    likes = item.get("likes", {}).get("summary", {}).get("total_count", 0)
    comments = item.get("comments", {}).get("summary", {}).get("total_count", 0)
    content = item.get("message") or item.get("caption") or ""
    return SocialPost(
        platform=platform,
        platform_post_id=item["id"],
        author_name="",
        title=content[:120],
        content=content,
        url=item.get("permalink_url") or item.get("permalink") or fallback_url,
        likes_count=likes or item.get("like_count", 0),
        comments_count=comments or item.get("comments_count", 0),
        published_at=item.get("created_time") or item.get("timestamp"),
    )
