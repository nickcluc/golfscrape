"""Proof of concept: pull your own Arccos data with Crawl4AI.

Step 1 (once):  python arccos_poc.py login
    Opens a real browser. Log in to the Arccos dashboard yourself,
    then press 'q' in this terminal (or close the browser). The session
    is saved to a local Crawl4AI profile, so your password never goes
    into this script.

Step 2:         python arccos_poc.py fetch [url ...]
    Re-uses the saved session, loads each dashboard page, and saves:
      output/<page>.md          readable text of the page
      output/api/<n>.json       every JSON response the page loaded
                                (this is where the real data is)
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.browser_profiler import BrowserProfiler

PROFILE = "arccos"
DASHBOARD = "https://dashboard.arccosgolf.com/"
OUT = Path(__file__).parent / "output"


async def login():
    print(f"A browser will open. Go to {DASHBOARD}, log in, then press 'q' here.")
    path = await BrowserProfiler().create_profile(
        profile_name=PROFILE,
        browser_config=BrowserConfig(headless=False),
    )
    print(f"Saved login profile to: {path}")


def slug(url):
    p = urlparse(url)
    s = re.sub(r"[^A-Za-z0-9]+", "_", (p.path + "_" + p.fragment).strip("/#")).strip("_")
    return s or "home"


async def fetch(urls):
    profile = BrowserProfiler().get_profile_path(PROFILE)
    if not profile:
        sys.exit("No saved login. Run: python arccos_poc.py login")

    browser = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        user_data_dir=profile,
    )
    run = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        capture_network_requests=True,  # grab the JSON the app fetches
        wait_until="networkidle",
        delay_before_return_html=5,     # let the single-page app finish loading
        page_timeout=60000,
    )

    (OUT / "api").mkdir(parents=True, exist_ok=True)
    n = 0
    async with AsyncWebCrawler(config=browser) as crawler:
        for url in urls:
            result = await crawler.arun(url=url, config=run)
            if not result.success:
                print(f"FAILED {url}: {result.error_message}")
                continue

            name = slug(url)
            (OUT / f"{name}.md").write_text(str(result.markdown or ""))
            print(f"{url} -> output/{name}.md")
            if "log in" in str(result.markdown).lower()[:2000]:
                print("  (looks like a login page: session may have expired, re-run 'login')")

            for ev in result.network_requests or []:
                if ev.get("event_type") != "response":
                    continue
                ctype = ev.get("headers", {}).get("content-type", "")
                text = (ev.get("body") or {}).get("text")
                if "json" not in ctype or not text:
                    continue
                try:
                    data = json.loads(text)
                except ValueError:
                    continue
                n += 1
                (OUT / "api" / f"{n:03d}.json").write_text(
                    json.dumps({"url": ev["url"], "status": ev.get("status"), "data": data}, indent=2)
                )
                print(f"  api/{n:03d}.json  {ev['url'][:110]}")

    print(f"\nDone. {n} JSON responses saved in {OUT / 'api'}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "login":
        asyncio.run(login())
    elif cmd == "fetch":
        asyncio.run(fetch(sys.argv[2:] or [DASHBOARD]))
    else:
        print(__doc__)
