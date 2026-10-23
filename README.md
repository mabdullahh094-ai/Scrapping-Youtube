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

The app uses live data only; demo records are disabled. Add the relevant API
credentials to `.env` for each platform. The UI supports a custom maximum or **All available**,
which follows YouTube pagination until the API returns no further page. There is
no truly infinite result set: YouTube controls pagination, search availability,
and daily API quota.

## Design

- The YouTube collector returns the normalized `SocialPost` model.
- Reddit, X, Instagram, Facebook Pages, and TikTok collectors use official APIs.
- The ScrapFly mode uses the cloned `ScrapFly-Scrapers` examples for public
  targets. Configure `SCRAPFLY_KEY` and `SCRAPFLY_SCRAPERS_PATH`; each platform
  has its own target field in the sidebar.
- SQLite stores records with a unique `(platform, platform_post_id)` key.
- Missing credentials appear as `not configured`; API and request errors appear as
  `failed` in the Streamlit status table. ScrapFly anti-bot blocks appear as
  `blocked by provider`.

Supported environment variables are `YOUTUBE_API_KEY`, `REDDIT_CLIENT_ID`,
`REDDIT_CLIENT_SECRET`, optional `REDDIT_USER_AGENT`, `X_BEARER_TOKEN`,
`META_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`, `INSTAGRAM_BUSINESS_ACCOUNT_ID`, and
`TIKTOK_ACCESS_TOKEN`. Instagram and Facebook do not provide arbitrary public
keyword search through this integration; the collector fetches authorized
account/page media and filters captions/messages locally. TikTok Research API
access requires approval from TikTok.

Only collect public data permitted by each platform's terms and API policy.
