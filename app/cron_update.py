from __future__ import annotations

import asyncio

from .db import init_db, upsert_cars
from .scraper import scrape_encar


def main() -> None:
    init_db()
    items = asyncio.run(scrape_encar(min_items=15))
    upsert_cars(items)


if __name__ == "__main__":
    main()
