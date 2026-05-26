# ============================================================
# gpc.py  — GPC / GEPHA სქრეიფერი (Playwright Chromium)
# GPC — Next.js / Dynamic rendered JS
# ============================================================
from __future__ import annotations

import time
import json
import random
from bs4 import BeautifulSoup
from datetime import datetime

from config import (
    GPC_LIST_URL, MAX_PAGES_GPC, PW_TIMEOUT, PW_WAIT_MS,
    COL_NAME, COL_PRICE, COL_OLD_PRICE, COL_DISCOUNT,
    COL_BRAND, COL_CATEGORY, COL_SOURCE, COL_URL, COL_UPDATED, COL_NORM_KEY,
)
from common import parse_price, normalize_key, extract_brand, classify_subcategory, calc_discount_pct


def _parse_page(soup: BeautifulSoup, page_url: str) -> list[dict]:
    records = []

    # 1. ვამოწმებთ Next.js JSON სტრუქტურას (GPC-ს ახალი პლატფორმა)
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data:
        try:
            data = json.loads(next_data.string)
            products = data.get("props", {}).get("pageProps", {}).get("products", [])
            if products:
                for prod in products:
                    name = prod.get("name", "").strip() or prod.get("title", "").strip()
                    if not name: 
                        continue
                    price = float(prod.get("price", 0))
                    old_price = float(prod.get("old_price", 0)) if prod.get("old_price") else None
                    
                    prod_id = prod.get("id") or prod.get("slug")
                    href = f"https://gpc.ge{prod_id}" if prod_id else page_url

                    records.append({
                        COL_NAME:      name[:100],
                        COL_PRICE:     price,
                        COL_OLD_PRICE: old_price if (old_price and old_price > price) else None,
                        COL_DISCOUNT:  calc_discount_pct(old_price, price),
                        COL_BRAND:     extract_brand(name),
                        COL_CATEGORY:  classify_subcategory(name),
                        COL_SOURCE:    "GPC",
                        COL_URL:       href,
                        COL_NORM_KEY:  normalize_key(name),
                        COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                return records
        except Exception:
            pass

    # 2. ალტერნატიული გზა: ახალი HTML ტექსტური სელექტორები (ლარის "₾" ნიშნით)
    price_tags = soup.find_all(string=lambda text: text and " ₾" in text)
    for price_tag in price_tags:
        price_container = price_tag.parent
        if not price_container: continue
        card = price_container.find_parent("div")
        if not card: continue

        name_el = card.find(string=lambda text: text and " - " in text)
        if not name_el:
            name_elements = [s.strip() for s in card.stripped_strings if len(s.strip()) > 5 and "₾" not in s]
            name = name_elements[0] if name_elements else None
        else:
            name = name_el.strip()

        if not name or len(name) < 2: continue
        if any(r[COL_NAME] == name[:100] for r in records): continue

        price = parse_price(price_tag)
        if price is None: continue

        old_price = None
        all_prices = card.find_all(string=lambda text: text and "₾" in text)
        for p_str in all_prices:
            if " ₾" not in p_str:
                parsed_old = parse_price(p_str)
                if parsed_old and parsed_old > price:
                    old_price = parsed_old
                    break

        link_el = card.select_one("a[href*='product']") or card.select_one("a[href*='medicament']") or card.select_one("a[href]")
        href = link_el["href"] if link_el else page_url
        if href and not href.startswith("http"):
            href = "https://gpc.ge" + href

        records.append({
            COL_NAME:      name[:100],
            COL_PRICE:     price,
            COL_OLD_PRICE: old_price,
            COL_DISCOUNT:  calc_discount_pct(old_price, price),
            COL_BRAND:     extract_brand(name),
            COL_CATEGORY:  classify_subcategory(name),
            COL_SOURCE:    "GPC",
            COL_URL:       href,
            COL_NORM_KEY:  normalize_key(name),
            COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    return records


def scrape_gpc(max_pages: int = MAX_PAGES_GPC) -> list[dict]:
    """
    GPC — Playwright Chromium სქრეიფი.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    results: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="ka-GE",
        )
        page = context.new_page()

        for pg in range(1, max_pages + 1):
            url = f"{GPC_LIST_URL}&page={pg}"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=PW_TIMEOUT)
                page.wait_for_timeout(3000)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3);")
                page.wait_for_timeout(1000)
            except Exception:
                break

            soup = BeautifulSoup(page.content(), "lxml")
            page_records = _parse_page(soup, url)

            if not page_records:
                break

            results.extend(page_records)
            time.sleep(random.uniform(1.5, 3.0))

        browser.close()

    return results
