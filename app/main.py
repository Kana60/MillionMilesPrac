from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import clear_cars, init_db, last_updated_at, list_cars, upsert_cars
from .scraper import scrape_encar


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


app = FastAPI(title="Encar Catalog")
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def landing(request: Request) -> Any:
    cars = list_cars(limit=200)
    last = last_updated_at()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "cars": cars,
            "last_updated_at": last,
        },
    )


async def _run_update(force: bool) -> JSONResponse:
    try:
        last = last_updated_at()
        if (not force) and last is not None:
            age = datetime.now(timezone.utc) - last.astimezone(timezone.utc)
            if age < timedelta(days=1):
                return JSONResponse({"ok": True, "skipped": True})

        # Refresh snapshot: replace existing rows with the latest scrape.
        clear_cars()
        items = await scrape_encar(min_items=80)
        count = upsert_cars(items)
        return JSONResponse({"ok": True, "count": count, "skipped": False})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=502)


@app.post("/api/update-cars")
async def update_cars(force: bool = False) -> JSONResponse:
    return await _run_update(force=force)


@app.post("/api/cron/update-cars")
async def cron_update_cars() -> JSONResponse:
    return await _run_update(force=False)


@app.get("/api/cars")
def api_cars(limit: int = 200) -> JSONResponse:
    cars = list_cars(limit=limit)
    payload = {
        "ok": True,
        "count": len(cars),
        "items": [
            {
                "id": c.id,
                "make": c.make,
                "model": c.model,
                "year": c.year,
                "mileage": c.mileage,
                "price": c.price,
                "image": c.image,
                "source_url": c.source_url,
                "updated_at": c.updated_at.isoformat(),
            }
            for c in cars
        ],
    }
    return JSONResponse(payload)
