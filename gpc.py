# ============================================================
# gpc.py  — GPC / GEPHA სქრეიფერი (requests + BeautifulSoup)
# GPC სერვერ-საიდ HTML აბრუნებს — JS არ სჭირდება
# ============================================================
from __future__ import annotations

import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from config import (
    GPC_LIST_URL, HEADERS, MAX_PAGES_GPC,
    COL_NAME, COL_PRICE, COL_OLD_PRICE, COL_DISCOUNT,
    COL_BRAND, COL_CATEGORY, COL_SOURCE, COL_URL, COL_UPDATED, COL_NORM_KEY,
)
from common import parse_price, normalize_key, extract_brand, classify_subcategory, calc_discount_pct


def _parse_page(soup: BeautifulSoup, page_url: str) -> list[dict]:
    records = []

    # GPC product cards — multiple selector fallbacks
    cards = (
        soup.select("div.product-card") or
        soup.select("div[class*='ProductCard']") or
        soup.select("div[class*='product-item']") or
        soup.select("li.catalog-item") or
        soup.select("div.card")
    )

    for card in cards:
        # ── სახელი ──────────────────────────────────────────
        name_el = (
            card.select_one("a.product-name") or
            card.select_one("span.product-name") or
            card.select_one("[class*='name']") or
            card.select_one("[class*='title']") or
            card.select_one("h3") or
            card.select_one("h4")
        )
        if not name_el:
            continue
        name = name_el.get_text(" ", strip=True).strip()
        if len(name) < 2:
            continue

        # ── მიმდინარე ფასი ──────────────────────────────────
        # GPC ფასდაკლებულ ფასს "ins" ან "sale-price" კლასში ათავსებს
        price_el = (
            card.select_one("span.sale-price") or
            card.select_one("[class*='sale-price']") or
            card.select_one("[class*='current-price']") or
            card.select_one("span.price") or
            card.select_one("[class*='price']")
        )
        price = parse_price(price_el.get_text(" ", strip=True)) if price_el else None
        if price is None:
            continue

        # ── ძველი ფასი (ფასდაკლების წინ) ─────────────────
        old_el = (
            card.select_one("span.old-price") or
            card.select_one("[class*='old-price']") or
            card.select_one("del") or
            card.select_one("s")
        )
        old_price = parse_price(old_el.get_text(" ", strip=True)) if old_el else None

        # ── ლინკი ───────────────────────────────────────────
        link_el = card.select_one("a[href]")
        href = link_el["href"] if link_el else page_url
        if href and not href.startswith("http"):
            href = "https://gpc.ge" + href

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
            COL_SOURCE:    "GPC",
            COL_URL:       href,
            COL_NORM_KEY:  normalize_key(name),
            COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    return records


def scrape_gpc(max_pages: int = MAX_PAGES_GPC) -> list[dict]:
    """
    GPC-ს ყველა გვერდი — პირველ ცარიელ გვერდზე ჩერდება.
    """
    results: list[dict] = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(1, max_pages + 1):
        url = f"{GPC_LIST_URL}&page={page}"
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
        except Exception:
            break

        soup = BeautifulSoup(resp.text, "lxml")
        page_records = _parse_page(soup, url)

        if not page_records:
            break   # გვერდები ამოიწურა

        results.extend(page_records)
        time.sleep(random.uniform(0.4, 0.9))

    return results
