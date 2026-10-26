"""Streamlit entry point for the multi-platform public data collector."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from services.database import initialize_database, load_posts, save_posts
from services.runner import run_all_collectors


load_dotenv()
st.set_page_config(page_title="Social Media Collector", page_icon=":mag:", layout="wide")
initialize_database()

st.title("Social Media Data Collector")
st.caption("Collect public, API-permitted data from multiple platforms in parallel.")

with st.sidebar:
    st.header("Collection settings")
    st.caption("Targets are sent to the configured Apify Actors. Do not enter passwords.")
    query = st.text_input(
        "YouTube keyword",
        placeholder="python programming",
        key="target_youtube",
    )
    st.text_input("Reddit subreddit", placeholder="python", key="target_reddit")
    st.text_input("Instagram username", placeholder="natgeo", key="target_instagram")
    st.text_input(
        "Facebook Marketplace query", placeholder="laptop", key="target_facebook"
    )
    st.text_input("TikTok keyword", placeholder="python", key="target_tiktok")
    st.text_input(
        "LinkedIn public profile URL",
        placeholder="https://www.linkedin.com/in/williamhgates",
        key="target_linkedin",
    )
    st.text_input(
        "X profile or post URL",
        placeholder="https://x.com/user",
        key="target_x",
    )
    use_keyword_fallback = st.checkbox(
        "Use YouTube keyword for blank platform targets",
        value=True,
        help="Uses the YouTube keyword for Reddit, Instagram, Facebook, and TikTok "
        "when their target field is blank.",
    )
    targets = {
        platform: str(st.session_state.get(f"target_{platform}", "")).strip()
        for platform in (
            "youtube",
            "reddit",
            "instagram",
            "facebook",
            "tiktok",
            "linkedin",
            "x",
        )
    }
    if use_keyword_fallback:
        for platform in ("reddit", "instagram", "facebook", "tiktok"):
            if not targets[platform]:
                targets[platform] = targets["youtube"]
    result_mode = st.selectbox(
        "Number of results",
        options=["All available", "Custom limit"],
        help="All available follows YouTube pagination until no more results remain.",
    )
    limit = (
        None
        if result_mode == "All available"
        else st.number_input("Maximum results", min_value=1, max_value=500, value=50)
    )
    st.warning(
        "Live Apify mode active. Each Actor uses your Apify credits; "
        "avoid repeated runs if quota is limited."
    )

if st.button("Collect from all platforms", type="primary"):
    if not any(value.strip() for value in targets.values()):
        st.warning("Enter at least one platform target first.")
    else:
        with st.spinner("Running collectors in parallel..."):
            report = run_all_collectors(
                query=query.strip(),
                limit=None if limit is None else int(limit),
                targets=targets,
            )

        successful_posts = [
            post for result in report.results for post in result.posts
        ]
        save_posts(successful_posts)

        status_rows = [
            {
                "Platform": result.platform,
                "Target configured": bool(targets.get(result.platform)),
                "Status": result.status,
                "Records": len(result.posts),
                "Error": result.error or "",
            }
            for result in report.results
        ]
        st.subheader("Collector status")
        st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)

        if report.posts:
            st.success(f"Collected {len(report.posts)} records.")
            posts_frame = pd.DataFrame([post.to_dict() for post in report.posts])
            st.subheader("Collected posts")
            platform_filter = st.multiselect(
                "Filter by platform",
                options=sorted(posts_frame["platform"].unique()),
                default=sorted(posts_frame["platform"].unique()),
            )
            filtered = posts_frame[posts_frame["platform"].isin(platform_filter)]
            st.dataframe(filtered, use_container_width=True, hide_index=True)
            st.download_button(
                "Download CSV",
                data=filtered.to_csv(index=False).encode("utf-8"),
                file_name="social_posts.csv",
                mime="text/csv",
            )
        else:
            st.info("No records were collected. Check the status table for details.")

saved_posts = load_posts()
if saved_posts:
    st.divider()
    st.subheader("Previously saved records")
    st.caption(
        "These records are loaded from the local database; viewing them does not "
        "use Apify credits."
    )
    saved_frame = pd.DataFrame([post.to_dict() for post in saved_posts])
    saved_platform_filter = st.multiselect(
        "Saved records platform filter",
        options=sorted(saved_frame["platform"].unique()),
        default=sorted(saved_frame["platform"].unique()),
        key="saved_platform_filter",
    )
    saved_filtered = saved_frame[
        saved_frame["platform"].isin(saved_platform_filter)
    ]
    st.dataframe(saved_filtered, use_container_width=True, hide_index=True)
    st.download_button(
        "Download saved CSV",
        data=saved_filtered.to_csv(index=False).encode("utf-8"),
        file_name="saved_social_posts.csv",
        mime="text/csv",
        key="download_saved_csv",
    )
