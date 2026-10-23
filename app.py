"""Streamlit entry point for the multi-platform public data collector."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from services.database import initialize_database, save_posts
from services.runner import run_all_collectors


load_dotenv()
st.set_page_config(page_title="Social Media Collector", page_icon=":mag:", layout="wide")
initialize_database()

st.title("Social Media Data Collector")
st.caption("Collect public, API-permitted data from multiple platforms in parallel.")

with st.sidebar:
    st.header("Collection settings")
    st.caption("Targets use public ScrapFly examples. Do not enter passwords or private URLs.")
    query = st.text_input("YouTube keyword", placeholder="python programming")
    targets = {
        "youtube": query,
        "reddit": st.text_input("Reddit subreddit", placeholder="python"),
        "instagram": st.text_input("Instagram username", placeholder="natgeo"),
        "facebook": st.text_input("Facebook Marketplace query", placeholder="laptop"),
        "tiktok": st.text_input("TikTok keyword", placeholder="python"),
        "x": st.text_input("X profile or post URL", placeholder="https://x.com/user"),
    }
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
    st.info("Live API/public data only. Demo records are disabled.")

if st.button("Collect from all platforms", type="primary"):
    if not any(value.strip() for value in targets.values()):
        st.warning("Enter at least one platform target first.")
    else:
        with st.spinner("Running collectors in parallel..."):
            report = run_all_collectors(
                query=query.strip(),
                limit=None if limit is None else int(limit),
                use_demo_data=False,
                targets=targets,
            )

        successful_posts = [
            post for result in report.results for post in result.posts
        ]
        save_posts(successful_posts)

        status_rows = [
            {
                "Platform": result.platform,
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
