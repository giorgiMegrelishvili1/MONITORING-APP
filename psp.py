# ============================================================
# psp.py  — PSP სქრეიფერი (Playwright headless Chromium)
# PSP — Magento-based, JS-rendered
# ============================================================
from __future__ import annotations

import time
import random
from bs4 import BeautifulSoup
from datetime import datetime

from config import (
    PSP_CATEGORY_URL, MAX_PAGES_PSP, PW_TIMEOUT, PW_WAIT_MS,
    COL_NAME, COL_PRICE, COL_OLD_PRICE, COL_DISCOUNT,
    COL_BRAND, COL_CATEGORY, COL_SOURCE, COL_URL, COL_UPDATED, COL_NORM_KEY,
)
from common import parse_price, normalize_key, extract_brand, classify_subcategory, calc_discount_pct


def _parse_psp_soup(soup: BeautifulSoup, page_url: str) -> list[dict]:
    records = []

    # Magento product item selectors
    cards = (
        soup.select("li.product-item") or
        soup.select("div.product-item-info") or
        soup.select("li[class*='item product']") or
        soup.select("div[class*='product-card']")
    )

    for card in cards:
        # ── სახელი ──────────────────────────────────────────
        name_el = (
            card.select_one("a.product-item-link") or
            card.select_one("strong.product-item-name a") or
            card.select_one("[class*='product-name'] a") or
            card.select_one("h2 a") or
            card.select_one("h3 a")
        )
        if not name_el:
            continue
        name = name_el.get_text(" ", strip=True).strip()
        if len(name) < 2:
            continue

        href = name_el.get("href", page_url)

        # ── მიმდინარე ფასი ──────────────────────────────────
        # Magento: special price → final price
        price_el = (
            card.select_one("[data-price-type='finalPrice'] span.price") or
            card.select_one("span.special-price span.price") or
            card.select_one("[class*='price-wrapper'] span.price") or
            card.select_one("span.price")
        )
        price = parse_price(price_el.get_text(" ", strip=True)) if price_el else None
        if price is None:
            continue

        # ── ძველი / რეგულარული ფასი ─────────────────────────
        old_el = (
            card.select_one("[data-price-type='regularPrice'] span.price") or
            card.select_one("span.old-price span.price") or
            card.select_one("del") or
            card.select_one("s")
        )
        old_price = parse_price(old_el.get_text(" ", strip=True)) if old_el else None
        if old_price and old_price <= price:
            old_price = None   # არ ჩაინიშნოს თუ ძველი <= ახალს

        brand    = extract_brand(name)
        subcat   = classify_subcategory(name)
        disc_pct = calc_discount_pct(old_price, price)

        records.append({
            COL_NAME:      name[:100],
            COL_PRICE:     price,
            COL_OLD_PRICE: old_price,
            COL_DISCOUNT:  disc_pct,
            COL_BRAND:     brand,
            COL_CATEGORY:  subcat,
            COL_SOURCE:    "PSP",
            COL_URL:       href,
            COL_NORM_KEY:  normalize_key(name),
            COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    return records


def scrape_psp(max_pages: int = MAX_PAGES_PSP) -> list[dict]:
    """
    PSP — Playwright headless Chromium სქრეიფი.
    Pagination: ?p=2, ?p=3 ...
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    results: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="ka-GE",
        )
        page = context.new_page()
        # სურათების ჩართვის გამორთვა — სიჩქარისთვის
        page.route("**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2}", lambda r: r.abort())

        for pg in range(1, max_pages + 1):
            url = PSP_CATEGORY_URL if pg == 1 else f"{PSP_CATEGORY_URL}?p={pg}"
            try:
                page.goto(url, wait_until="networkidle", timeout=PW_TIMEOUT)
                page.wait_for_timeout(PW_WAIT_MS)
            except Exception:
                break

            soup = BeautifulSoup(page.content(), "lxml")
            page_records = _parse_psp_soup(soup, url)

            if not page_records:
                break

            results.extend(page_records)
            time.sleep(random.uniform(0.5, 1.0))

        browser.close()

    return results
