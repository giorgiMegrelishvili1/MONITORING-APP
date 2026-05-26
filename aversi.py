# ============================================================
# aversi.py  — Aversi სქრეიფერი (Playwright headless Chromium)
# Aversi — WooCommerce-based, JS-rendered
# ============================================================
from __future__ import annotations

import time
import random
from bs4 import BeautifulSoup
from datetime import datetime

from config import (
    AVERSI_LIST_URL, MAX_PAGES_AVERSI, PW_TIMEOUT, PW_WAIT_MS,
    COL_NAME, COL_PRICE, COL_OLD_PRICE, COL_DISCOUNT,
    COL_BRAND, COL_CATEGORY, COL_SOURCE, COL_URL, COL_UPDATED, COL_NORM_KEY,
)
from common import parse_price, normalize_key, extract_brand, classify_subcategory, calc_discount_pct


def _parse_aversi_soup(soup: BeautifulSoup, page_url: str) -> list[dict]:
    records = []

    # WooCommerce selectors — Aversi
    cards = (
        soup.select("li.product") or
        soup.select("div.product-small") or
        soup.select("div[class*='product-grid-item']") or
        soup.select("div.product-wrapper") or
        soup.select("article[class*='product']")
    )

    for card in cards:
        # ── სახელი ──────────────────────────────────────────
        name_el = (
            card.select_one("p.product-title a") or
            card.select_one("h3.product-title a") or
            card.select_one("a.woocommerce-loop-product__link") or
            card.select_one("[class*='product-title'] a") or
            card.select_one("h3 a") or
            card.select_one("h4 a")
        )
        if not name_el:
            continue
        name = name_el.get_text(" ", strip=True).strip()
        if len(name) < 2:
            continue

        href = name_el.get("href", page_url)

        # ── ფასი — WooCommerce sale price ───────────────────
        # ფასდაკლება: <del> old, <ins> new
        ins_el = card.select_one("span.price ins span.amount")
        del_el = card.select_one("span.price del span.amount")

        if ins_el:
            price     = parse_price(ins_el.get_text(" ", strip=True))
            old_price = parse_price(del_el.get_text(" ", strip=True)) if del_el else None
        else:
            price_el  = (
                card.select_one("span.price span.amount") or
                card.select_one("span.amount") or
                card.select_one("[class*='price']")
            )
            price     = parse_price(price_el.get_text(" ", strip=True)) if price_el else None
            old_price = None

        if price is None:
            continue
        if old_price and old_price <= price:
            old_price = None

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
            COL_SOURCE:    "Aversi",
            COL_URL:       href,
            COL_NORM_KEY:  normalize_key(name),
            COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    return records


def scrape_aversi(max_pages: int = MAX_PAGES_AVERSI) -> list[dict]:
    """
    Aversi — Playwright headless Chromium სქრეიფი.
    Pagination: /page-2/ /page-3/ ...
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
        page.route("**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2}", lambda r: r.abort())

        for pg in range(1, max_pages + 1):
            url = AVERSI_LIST_URL if pg == 1 else f"{AVERSI_LIST_URL}page-{pg}/"
            try:
                page.goto(url, wait_until="networkidle", timeout=PW_TIMEOUT)
                page.wait_for_timeout(PW_WAIT_MS)
            except Exception:
                break

            soup = BeautifulSoup(page.content(), "lxml")
            page_records = _parse_aversi_soup(soup, url)

            if not page_records:
                break

            results.extend(page_records)
            time.sleep(random.uniform(0.5, 1.0))

        browser.close()

    return results
