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

The app uses live data only; demo records are disabled. Add `YOUTUBE_API_KEY` to
`.env` for YouTube search. The UI supports a custom maximum or **All available**,
which follows YouTube pagination until the API returns no further page. There is
no truly infinite result set: YouTube controls pagination, search availability,
and daily API quota.

## Design

- The YouTube collector returns the normalized `SocialPost` model.
- SQLite stores records with a unique `(platform, platform_post_id)` key.
- API errors are shown in the Streamlit status table.

Only collect public data permitted by each platform's terms and API policy.
