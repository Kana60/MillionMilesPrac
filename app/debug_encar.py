from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

from playwright.async_api import async_playwright


URL = "https://www.encar.com/dc/dc_carsearchlist.do"


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1440, "height": 900},
        )
        page = await context.new_page()

        json_hits: List[Dict[str, Any]] = []

        async def on_response(resp) -> None:
            try:
                ct = (resp.headers.get("content-type") or "").lower()
                if "application/json" not in ct:
                    return
                u = resp.url
                if "encar.com" not in u:
                    return
                if "dc_" not in u and "carsearch" not in u and "search" not in u:
                    return
                data = await resp.json()
                json_hits.append({"url": u, "keys": list(data)[:50], "sample": data})
            except Exception:
                return

        page.on("response", on_response)

        await page.goto(URL, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)

        print("Title:", await page.title())
        print("JSON hits:", len(json_hits))
        for i, hit in enumerate(json_hits[:5]):
            print("---", i)
            print(hit["url"])
            print("keys:", hit["keys"])
            # print small sample
            try:
                print(json.dumps(hit["sample"], ensure_ascii=False)[:2000])
            except Exception:
                pass

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
