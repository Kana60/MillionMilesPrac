from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Car:
    id: str
    make: str
    model: str
    year: int
    mileage: int
    price: int
    image: str
    source_url: Optional[str]
    updated_at: datetime


@dataclass(frozen=True)
class ScrapedCar:
    make: str
    model: str
    year: int
    mileage: int
    price: int
    image: str
    source_url: Optional[str] = None
