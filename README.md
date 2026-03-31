# Encar Car Catalog (Python)

FastAPI + Playwright scraper + SQLite storage + premium landing page.

## Features

- Scrapes Encar (dynamic) for at least 10–15 cars: make, model, year, mileage, price, image.
- Stores results in SQLite (`app/data/cars.db`) with upsert.
- `POST /api/update-cars` triggers a refresh (cron-friendly).
- Landing page `/` shows a responsive grid inspired by millionmiles.ae UX.
- Fallback seed data if scraping is blocked or selectors change.

## Setup

1. Create & activate venv

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Install Playwright browsers (required)

```bash
playwright install chromium
```

4. Run the app

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Updating cars

Trigger a scrape manually:

```bash
curl -X POST http://127.0.0.1:8000/api/update-cars
```

## Daily update (1x сутки)

### Option A: Windows Task Scheduler

Create a daily task that runs PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/update-cars
```

### Option B: Cron (Linux)

```cron
0 3 * * * curl -X POST https://YOUR_DOMAIN/api/update-cars
```

## Notes

- Encar may block automated browsing. The scraper uses a realistic User-Agent, extra headers, and `wait_until=\"networkidle\"`. If blocked, the app uses `seed` data so UI is never empty.
