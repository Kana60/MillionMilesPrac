from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional

import httpx

from .models import ScrapedCar


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def _to_int(value: str) -> int:
    digits = re.sub(r"[^0-9]", "", value or "")
    return int(digits) if digits else 0


def _split_make_model(title: str) -> tuple[str, str]:
    t = re.sub(r"\s+", " ", (title or "").strip())
    if not t:
        return ("Unknown", "Unknown")
    parts = t.split(" ")
    if len(parts) == 1:
        return (parts[0], "")
    return (parts[0], " ".join(parts[1:]))


def _encar_image_url(location: str) -> str:
    if not location:
        return ""
    if location.startswith("http://") or location.startswith("https://"):
        return location
    # Encar images are typically served from ci.encar.com
    if location.startswith("/"):
        return "https://ci.encar.com" + location
    return "https://ci.encar.com/" + location


def _price_to_krw(price_value: Any) -> int:
    """Encar API `Price` is typically in 만원 units (10,000 KRW)."""
    try:
        v = float(price_value)
    except Exception:
        return 0
    if math.isnan(v) or v <= 0:
        return 0
    return int(v * 10000)


def _year_to_int(year_value: Any, form_year_value: Any) -> int:
    """Prefer FormYear (e.g. '2023'). Fallback: Year like 202311.0 -> 2023."""
    try:
        fy = int(str(form_year_value).strip())
        if 1900 <= fy <= 2100:
            return fy
    except Exception:
        pass
    try:
        y = int(float(year_value))
        if y > 10000:
            return int(str(y)[:4])
        if 1900 <= y <= 2100:
            return y
    except Exception:
        pass
    return 0


async def scrape_encar(min_items: int = 12, timeout_ms: int = 45000) -> List[ScrapedCar]:
    """Scrape cars from Encar.

    Implementation detail:
    - We use the same API endpoint the site uses (api.encar.com).
    - This provides reliable structured fields and real photo URLs.
    """

    try:
        # Encar API endpoint used by the website.
        # NOTE: Parameters may evolve; if this breaks, re-capture from network logs.
        # sr format: |<sortKey>|<offset>|<limit>
        target = max(int(min_items), 1)
        page_limit = min(max(target, 12), 50)
        base_url = (
            "https://api.encar.com/search/car/list/general"
            "?count=true"
            "&q=(And.(And.Hidden.N._.CarType.Y.)_.(Or.ServiceMark.EncarDiagnosisP0._.ServiceMark.EncarDiagnosisP1._.ServiceMark.EncarDiagnosisP2.))"
        )

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.encar.com",
            "Referer": "https://www.encar.com/dc/dc_carsearchlist.do",
            "Accept-Language": "en-US,en;q=0.9,ko-KR;q=0.8,ko;q=0.7",
        }

        timeout_s = max(int(timeout_ms / 1000), 10)
        async with httpx.AsyncClient(headers=headers, timeout=timeout_s, follow_redirects=True) as client:
            scraped: List[ScrapedCar] = []
            seen_ids: set[str] = set()

            # Some environments return fewer than requested per page; paginate until we have enough.
            max_pages = max(1, int(math.ceil(target / page_limit)) + 6)
            for page in range(max_pages):
                offset = page * page_limit
                api_url = base_url + f"&sr=%7CExtendWarranty%7C{offset}%7C{page_limit}"

                resp = await client.get(api_url)
                resp.raise_for_status()
                payload = resp.json()

                if not isinstance(payload, dict):
                    raise RuntimeError("Unexpected Encar API response type")

                results = payload.get("SearchResults") or []
                if not isinstance(results, list) or len(results) == 0:
                    break

                added_this_page = 0
                for row in results:
                    cid = str(row.get("Id") or "").strip()
                    if cid and cid in seen_ids:
                        continue

                    make = str(row.get("Manufacturer") or "").strip() or "Unknown"
                    model_main = str(row.get("Model") or "").strip()
                    badge = str(row.get("Badge") or "").strip()
                    model = (model_main + (" " + badge if badge else "")).strip() or "Unknown"

                    year = _year_to_int(row.get("Year"), row.get("FormYear"))
                    mileage = int(float(row.get("Mileage") or 0))
                    price = _price_to_krw(row.get("Price"))

                    photos = row.get("Photos") or []
                    img_loc = ""
                    if isinstance(photos, list) and photos:
                        img_loc = str((photos[0] or {}).get("location") or "").strip()
                    if not img_loc:
                        # Some responses provide `Photo` prefix rather than explicit list
                        img_loc = str(row.get("Photo") or "").strip()
                        if img_loc and not img_loc.endswith(".jpg"):
                            img_loc = img_loc + "001.jpg"

                    image = _encar_image_url(img_loc)
                    if not image:
                        continue

                    source_url = (
                        f"https://www.encar.com/dc/dc_cardetailview.do?carid={cid}" if cid else None
                    )
                    scraped.append(
                        ScrapedCar(
                            make=make,
                            model=model,
                            year=year,
                            mileage=mileage,
                            price=price,
                            image=image,
                            source_url=source_url,
                        )
                    )
                    added_this_page += 1
                    if cid:
                        seen_ids.add(cid)
                    if len(scraped) >= target:
                        return scraped[:target]

                if added_this_page == 0:
                    break

            raise RuntimeError(f"Encar returned too few parsed items: {len(scraped)} (need >= {target})")

    except Exception as e:
        msg = str(e).strip()
        if not msg:
            msg = repr(e)
        raise RuntimeError(f"Encar scrape failed ({type(e).__name__}): {msg}") from e
