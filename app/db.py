from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from .models import Car, ScrapedCar


DB_PATH = Path(__file__).parent / "data" / "cars.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cars (
                id TEXT PRIMARY KEY,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                mileage INTEGER NOT NULL,
                price INTEGER NOT NULL,
                image TEXT NOT NULL,
                source_url TEXT,
                updated_at TEXT NOT NULL
            );
            """
        )
        # Backward compatible migration for older DB files.
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(cars);").fetchall()}
        if "source_url" not in cols:
            conn.execute("ALTER TABLE cars ADD COLUMN source_url TEXT;")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cars_updated_at ON cars(updated_at DESC);")


def stable_car_id(item: ScrapedCar) -> str:
    # IMPORTANT:
    # Do not include `image` in the ID.
    # Image URLs can change between updates (especially when using dynamic sources),
    # which would create new IDs and duplicate rows.
    if item.source_url:
        raw = f"encar|{item.source_url}".encode("utf-8")
    else:
        raw = f"{item.make}|{item.model}|{item.year}|{item.mileage}|{item.price}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def dedupe_cars() -> int:
    """Remove duplicate cars keeping the most recently updated row per core fields."""
    with _connect() as conn:
        cur = conn.execute(
            """
            WITH ranked AS (
              SELECT
                id,
                ROW_NUMBER() OVER (
                  PARTITION BY make, model, year, mileage, price
                  ORDER BY updated_at DESC
                ) AS rn
              FROM cars
            )
            DELETE FROM cars
            WHERE id IN (SELECT id FROM ranked WHERE rn > 1);
            """
        )
        # sqlite3 returns -1 for rowcount in some cases; compute via changes().
        changes = conn.execute("SELECT changes();").fetchone()[0]
        conn.commit()
        return int(changes)


def clear_cars() -> int:
    with _connect() as conn:
        conn.execute("DELETE FROM cars;")
        changes = conn.execute("SELECT changes();").fetchone()[0]
        conn.commit()
        return int(changes)


def last_updated_at() -> datetime | None:
    with _connect() as conn:
        row = conn.execute("SELECT MAX(updated_at) AS m FROM cars;").fetchone()
        if not row:
            return None
        v = row["m"]
        if not v:
            return None
        try:
            return datetime.fromisoformat(v)
        except Exception:
            return None


def upsert_cars(items: Iterable[ScrapedCar]) -> int:
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for it in items:
        cid = stable_car_id(it)
        rows.append(
            (
                cid,
                it.make,
                it.model,
                int(it.year),
                int(it.mileage),
                int(it.price),
                it.image,
                it.source_url,
                now,
            )
        )

    with _connect() as conn:
        conn.executemany(
            """
            INSERT INTO cars (id, make, model, year, mileage, price, image, source_url, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                make=excluded.make,
                model=excluded.model,
                year=excluded.year,
                mileage=excluded.mileage,
                price=excluded.price,
                image=excluded.image,
                source_url=excluded.source_url,
                updated_at=excluded.updated_at;
            """,
            rows,
        )
        conn.commit()

    # Clean up any existing duplicates that may have been created previously.
    dedupe_cars()
    return len(rows)


def list_cars(limit: int = 60) -> List[Car]:
    with _connect() as conn:
        cur = conn.execute(
            """
            SELECT id, make, model, year, mileage, price, image, source_url, updated_at
            FROM cars
            ORDER BY updated_at DESC
            LIMIT ?;
            """,
            (limit,),
        )
        out: List[Car] = []
        for r in cur.fetchall():
            out.append(
                Car(
                    id=r["id"],
                    make=r["make"],
                    model=r["model"],
                    year=int(r["year"]),
                    mileage=int(r["mileage"]),
                    price=int(r["price"]),
                    image=r["image"],
                    source_url=r["source_url"],
                    updated_at=datetime.fromisoformat(r["updated_at"]),
                )
            )
        return out
