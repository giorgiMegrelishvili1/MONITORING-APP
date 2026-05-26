# ============================================================
# aversi.py  — Aversi სქრეიფერი (Playwright Chromium)
# Aversi — Next.js / React-based API data rendering
# ============================================================
from __future__ import annotations

import time
import json
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

    # 1. საუკეთესო გზა: მონაცემების ამოღება პირდაპირ Next.js-ის შიდა JSON სკრიპტიდან
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data:
        try:
            data = json.loads(next_data.string)
            # ვეძებთ პროდუქტების სიას Next.js-ის props სტრუქტურაში
            page_props = data.get("props", {}).get("pageProps", {})
            products = (
                page_props.get("products", []) or 
                page_props.get("initialState", {}).get("products", []) or
                page_props.get("data", {}).get("items", [])
            )
            
            if products:
                for prod in products:
                    name = prod.get("name", "").strip() or prod.get("title", "").strip()
                    if not name: 
                        continue
                        
                    price = float(prod.get("price", 0))
                    old_price = float(prod.get("old_price", 0)) if prod.get("old_price") else None
                    
                    # ლინკის აწყობა (id-ის ან slug-ის მიხედვით)
                    prod_id = prod.get("id") or prod.get("slug")
                    href = f"https://aversi.ge{prod_id}" if prod_id else page_url
                    
                    records.append({
                        COL_NAME:      name[:100],
                        COL_PRICE:     price,
                        COL_OLD_PRICE: old_price if (old_price and old_price > price) else None,
                        COL_DISCOUNT:  calc_discount_pct(old_price, price),
                        COL_BRAND:     extract_brand(name) or prod.get("brand", {}).get("name", ""),
                        COL_CATEGORY:  classify_subcategory(name),
                        COL_SOURCE:    "Aversi",
                        COL_URL:       href,
                        COL_NORM_KEY:  normalize_key(name),
                        COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                return records
        except Exception:
            pass

    # 2. ალტერნატიული გზა: ახალი დინამიური HTML სელექტორები (თუ JSON ჩავარდა)
    cards = (
        soup.select("div[class*='product-card']") or 
        soup.select("div[class*='ProductCard']") or
        soup.select("div[class*='item-wrapper']") or
        soup.select(".grid > div")
    )

    for card in cards:
        # ვეძებთ პროდუქტის სათაურს
        name_el = card.select_one("h3") or card.select_one("h4") or card.select_one("p") or card.select_one("a[href*='product']")
        if not name_el:
            continue
        name = name_el.get_text(" ", strip=True).strip()
        if len(name) < 2 or "₾" in name:
            continue

        href_el = card.select_one("a")
        href = href_el.get("href", page_url) if href_el else page_url
        if href and not href.startswith("http"):
            href = "https://aversi.ge" + href

        # ფასების ამოღება ლარის "₾" ნიშნის მიხედვით
        price_tags = card.find_all(string=lambda text: text and "₾" in text)
        if not price_tags:
            continue
            
        prices = [parse_price(p) for p in price_tags if parse_price(p) is not None]
        if not prices:
            continue
            
        price = prices[0]
        old_price = prices[1] if len(prices) > 1 and prices[1] > price else None

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
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    results: list[dict] = []

    with sync_playwright() as p:
        # იუზერის რეალური ქცევის სიმულაცია ანტი-ბოტისთვის
        browser = p.chromium.launch(
            headless=True, 
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="ka-GE",
        )
        page = context.new_page()
        
        # ⚠️ ყურადღება: სურათების ბლოკირება წავშალეთ Cloudflare-ის თავიდან ასაცილებლად!

        for pg in range(1, max_pages + 1):
            # Next.js საიტებზე პაგინაცია ძირითადად მუშაობს ?page= პარამეტრით
            url = AVERSI_LIST_URL if pg == 1 else f"{AVERSI_LIST_URL}?page={pg}"
            if "page-" in AVERSI_LIST_URL:
                url = AVERSI_LIST_URL if pg == 1 else f"{AVERSI_LIST_URL}page-{pg}/"

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=PW_TIMEOUT)
                page.wait_for_timeout(3000) # ვაცდით JS-ს მონაცემების ჩატვირთვას
                
                # იმიტაციური სქროლი "Lazy loading"-ის ასამუშავებლად
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3);")
                page.wait_for_timeout(1000)
            except Exception:
                break

            soup = BeautifulSoup(page.content(), "lxml")
            page_records = _parse_aversi_soup(soup, url)

            if not page_records:
                # თუ ვერაფერი იპოვა, კიდევ ერთხელ დაველოდოთ დინამიურ HTML-ს
                page.wait_for_timeout(2000)
                soup = BeautifulSoup(page.content(), "lxml")
                page_records = _parse_aversi_soup(soup, url)
                if not page_records:
                    break

            results.extend(page_records)
            time.sleep(random.uniform(1.5, 3.0))

        browser.close()

    return results
