# activitydigest

Weekly email updates with toddler-friendly things to do on the weekend.

## What it does

- Fetches candidate events from the Ticketmaster Discovery API and local event feeds
- Filters and ranks them with Claude based on toddler appropriateness
- Sends a curated weekly digest by email
- Runs automatically via GitHub Actions on a cron schedule

## Files

- `main.py` — pipeline entry point
- `fetch_events.py` — gather raw event candidates
- `score_events.py` — filter and rank with Claude
- `send_digest.py` — send the HTML digest via Gmail API
- `config.example.yaml` — template config for local testing
- `.github/workflows/weekly-digest.yml` — cron job configuration

## Setup

1. Copy the example config:

```bash
cp config.example.yaml config.yaml
```

2. Update the values in `config.yaml` with your city, API keys, and email.

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run locally:

```bash
python main.py
```

## Required environment variables

For GitHub Actions, set these secrets/variables:

- Secrets: `ANTHROPIC_API_KEY`, `TICKETMASTER_API_KEY`, `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `DIGEST_EMAIL_TO`
- Variables: `EVENT_CITY`, `EVENT_STATE`, `EVENT_RADIUS`, `CHILD_AGE_RANGE`

The workflow runs every Thursday at 22:00 UTC by default.
