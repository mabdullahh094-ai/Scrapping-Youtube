# Social Media Data Collector

Streamlit application for collecting public YouTube records through the
official YouTube Data API.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

The app uses live Apify Actor collection. Add `APIFY_API_TOKEN` and one
`APIFY_ACTOR_<PLATFORM>` value for each platform you want to collect in `.env`.
Actor input schemas differ, so use `APIFY_INPUT_<PLATFORM>` for a JSON input
override when an Actor does not use the defaults in
`collectors/apify_collector.py`.
The UI supports a custom maximum or **All available**,
which follows YouTube pagination until the API returns no further page. There is
no truly infinite result set: YouTube controls pagination, search availability,
and daily API quota.

## Design

- The YouTube collector returns the normalized `SocialPost` model.
- Reddit, X, Instagram, Facebook Pages, and TikTok collectors use official APIs.
- LinkedIn public profile URLs are supported through a configured Apify Actor.
- The Apify mode runs each configured Actor through Apify's
  `run-sync-get-dataset-items` endpoint and normalizes its dataset records.
  Each platform has its own Actor ID and target field in the sidebar.
- SQLite stores records with a unique `(platform, platform_post_id)` key.
- Saved records are always shown from `data/social_media.db`, including when
  live provider credits are unavailable.
- Missing credentials appear as `not configured`; API and request errors appear as
  `failed` in the Streamlit status table; valid requests with no returned
  items appear as `no records`.
- The status table also shows whether each platform target was configured.
- Facebook Marketplace records include a generated item URL when Facebook
  provides a listing ID.

Supported Apify variables are `APIFY_API_TOKEN`,
`APIFY_ACTOR_YOUTUBE`, `APIFY_ACTOR_REDDIT`, `APIFY_ACTOR_X`,
`APIFY_ACTOR_INSTAGRAM`, `APIFY_ACTOR_FACEBOOK`, `APIFY_ACTOR_TIKTOK`, and
`APIFY_ACTOR_LINKEDIN`. Actor input schemas and platform access vary by Actor;
configure `APIFY_INPUT_<PLATFORM>` when required.

Only collect public data permitted by each platform's terms and API policy.
