# ============================================================
# psp.py — PSP (psp.ge) სქრეიფერი
# PSP-ს საიტი მთლიანად კლიენტის მხარეს (JS) რენდერდება — მარტივი
# HTTP მოთხოვნა ცარიელ გვერდს აბრუნებს, ამიტომ აქ მართლა
# საჭიროა ნამდვილი ბრაუზერი (Playwright).
# ============================================================
from __future__ import annotations

import time
import json
import random
from bs4 import BeautifulSoup
from datetime import datetime

from config import (
    PSP_CATEGORY_URL, MAX_PAGES_PSP, PW_TIMEOUT,
    COL_NAME, COL_PRICE, COL_OLD_PRICE, COL_DISCOUNT,
    COL_BRAND, COL_CATEGORY, COL_SOURCE, COL_URL, COL_UPDATED, COL_NORM_KEY,
)
from common import (
    parse_price, parse_all_prices, normalize_key, extract_brand,
    classify_subcategory, calc_discount_pct, find_product_lists, get_field,
)


def _parse_psp_soup(soup: BeautifulSoup, page_url: str) -> list[dict]:
    records: list[dict] = []

    # 1. საუკეთესო გზა — ჩაშენებული JSON (Next.js/Nuxt-ტიპის საიტებზე)
    for script in soup.find_all("script"):
        raw = script.string
        if not raw or "price" not in raw.lower():
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        for lst in find_product_lists(data):
            for prod in lst:
                name = get_field(prod, {"name", "title"})
                price = get_field(prod, {"price", "currentprice", "current_price"})
                if not name or price in (None, ""):
                    continue
                try:
                    price = float(str(price).replace(",", "."))
                except (TypeError, ValueError):
                    continue
                old_raw = get_field(prod, {"oldprice", "old_price", "regularprice"})
                old_price = None
                if old_raw not in (None, ""):
                    try:
                        old_price = float(str(old_raw).replace(",", "."))
                    except (TypeError, ValueError):
                        old_price = None
                slug = get_field(prod, {"slug", "url", "id"})
                href = f"https://psp.ge{slug}" if slug and str(slug).startswith("/") else page_url

                records.append({
                    COL_NAME:      str(name)[:100],
                    COL_PRICE:     price,
                    COL_OLD_PRICE: old_price if (old_price and old_price > price) else None,
                    COL_DISCOUNT:  calc_discount_pct(old_price, price),
                    COL_BRAND:     extract_brand(str(name)),
                    COL_CATEGORY:  classify_subcategory(str(name)),
                    COL_SOURCE:    "PSP",
                    COL_URL:       href,
                    COL_NORM_KEY:  normalize_key(str(name)),
                    COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
        if records:
            return records

    # 2. ალტერნატივა — ვეძებთ პროდუქტის ბმულებს, რომელთა კონტეინერშიც ₾ სიმბოლოა
    candidate_links = (
        soup.select("a[href*='.html']") or
        soup.select("a[href*='/product']")
    )
    seen = set()
    for a in candidate_links:
        href = a.get("href", "")
        if not href or href in seen:
            continue
        name = a.get("title") or a.get_text(" ", strip=True)
        name = (name or "").strip()
        if len(name) < 3:
            continue

        container = a
        prices: list[float] = []
        for _ in range(5):
            container = container.parent
            if container is None:
                break
            blob = container.get_text(" ", strip=True)
            if "₾" in blob:
                prices = parse_all_prices(blob)
                if prices:
                    break
        if not prices:
            continue

        seen.add(href)
        price = min(prices)
        old_price = max(prices) if len(prices) > 1 and max(prices) > price else None
        full_href = href if href.startswith("http") else f"https://psp.ge{href}"

        records.append({
            COL_NAME:      name[:100],
            COL_PRICE:     price,
            COL_OLD_PRICE: old_price,
            COL_DISCOUNT:  calc_discount_pct(old_price, price),
            COL_BRAND:     extract_brand(name),
            COL_CATEGORY:  classify_subcategory(name),
            COL_SOURCE:    "PSP",
            COL_URL:       full_href,
            COL_NORM_KEY:  normalize_key(name),
            COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    return records


def scrape_psp(max_pages: int = MAX_PAGES_PSP) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    results: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="ka-GE",
        )
        page = context.new_page()

        for pg in range(1, max_pages + 1):
            url = PSP_CATEGORY_URL if pg == 1 else f"{PSP_CATEGORY_URL}?page={pg}"

            try:
                page.goto(url, wait_until="networkidle", timeout=PW_TIMEOUT)
                page.wait_for_timeout(2500)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/2);")
                page.wait_for_timeout(1000)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                page.wait_for_timeout(800)
            except Exception:
                break

            soup = BeautifulSoup(page.content(), "lxml")
            page_records = _parse_psp_soup(soup, url)

            if not page_records:
                page.wait_for_timeout(2000)
                soup = BeautifulSoup(page.content(), "lxml")
                page_records = _parse_psp_soup(soup, url)
                if not page_records:
                    break

            results.extend(page_records)

            if len(page_records) < 5:
                break

            time.sleep(random.uniform(1.0, 2.0))

        browser.close()

    return results
