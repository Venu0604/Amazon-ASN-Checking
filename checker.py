"""
Shared logic: given an Amazon.in hidden-keywords search URL, figure out
which of the ASINs in that URL don't show up in the search results.

Used by both check_missing.py (CLI) and dashboard.py (Streamlit UI).
"""

import time
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

MAX_PAGES = 10  # safety cap on pagination
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0.0.0 Safari/537.36")


def parse_asins_from_url(url):
    query = parse_qs(urlparse(url).query)
    values = query.get("hidden-keywords") or query.get("hidden-keywords[]")
    if not values:
        raise ValueError("No 'hidden-keywords' parameter found in that URL.")
    return [a.strip().upper() for a in values[0].split("|") if a.strip()]


def extract_asins_from_page(page):
    handles = page.query_selector_all("div[data-asin]")
    found = set()
    for h in handles:
        asin = (h.get_attribute("data-asin") or "").strip()
        if asin:
            found.add(asin)
    return found


def run_check(url, on_progress=None):
    """
    Runs the browser check against `url`.
    on_progress(message: str) is called with human-readable status updates.

    Returns a dict: {"asins": [...], "found": set(...), "present": [...], "missing": [...]}
    """
    def log(msg):
        if on_progress:
            on_progress(msg)

    asins = parse_asins_from_url(url)
    log(f"Parsed {len(asins)} ASINs from URL.")

    all_found = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=USER_AGENT,
            locale="en-IN",
            viewport={"width": 1280, "height": 1800},
        )
        page = context.new_page()
        page.goto(url, timeout=30000, wait_until="domcontentloaded")

        page_num = 1
        while page_num <= MAX_PAGES:
            log(f"Reading page {page_num} ...")
            try:
                page.wait_for_selector("div[data-asin]", timeout=10000)
            except Exception:
                log("No result tiles found (possibly blocked or no results).")
                break

            page_asins = extract_asins_from_page(page)
            new_asins = page_asins - all_found
            log(f"Page {page_num}: found {len(page_asins)} tiles ({len(new_asins)} new)")
            all_found |= page_asins

            next_link = page.query_selector("a.s-pagination-next:not(.s-pagination-disabled)")
            if not next_link:
                break

            next_link.click()
            page_num += 1
            time.sleep(2)  # be polite / let the next page settle

        browser.close()

    present = [a for a in asins if a in all_found]
    missing = [a for a in asins if a not in all_found]

    return {"asins": asins, "found": all_found, "present": present, "missing": missing}
