# ============================================================
# psp.py — განახლებული ვერსია PSP-ს ახალი საიტისთვის
# ============================================================
from __future__ import annotations

import time
import json
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

    # 1. ვცდილობთ მონაცემები ამოვიღოთ პირდაპირ Next.js-ის შიდა სკრიპტიდან (ყველაზე საიმედოა)
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data:
        try:
            data = json.loads(next_data.string)
            # აგვიანებს ან იცვლება სტრუქტურა? თუ იპოვა, გადავუყვებით პროდუქტებს JSON-ში
            # (თუ ეს მეთოდი ჩავარდა, ქვემოთ HTML სელექტორები დააზღვევს)
            products = data.get("props", {}).get("pageProps", {}).get("products", [])
            if products:
                for prod in products:
                    name = prod.get("name", "").strip()
                    if not name: continue
                    price = float(prod.get("price", 0))
                    old_price = float(prod.get("old_price", 0)) if prod.get("old_price") else None
                    href = f"https://psp.ge{prod.get('id')}"
                    
                    records.append({
                        COL_NAME:      name[:100],
                        COL_PRICE:     price,
                        COL_OLD_PRICE: old_price if (old_price and old_price > price) else None,
                        COL_DISCOUNT:  calc_discount_pct(old_price, price),
                        COL_BRAND:     extract_brand(name),
                        COL_CATEGORY:  classify_subcategory(name),
                        COL_SOURCE:    "PSP",
                        COL_URL:       href,
                        COL_NORM_KEY:  normalize_key(name),
                        COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                return records
        except Exception:
            pass

    # 2. ალტერნატიული გზა: ახალი CSS სელექტორები (თუ JSON არ დაგვხვდა)
    # PSP-ს ახალ საიტზე ბარათებს ხშირად აქვს კლასები: "product-card", "product_card" ან Tailwind-ის დივები
    cards = (
        soup.select("div[class*='product-card']") or 
        soup.select("div[class*='ProductCard']") or
        soup.select("article[class*='product']") or
        soup.select(".grid > div") # ბადის ელემენტები
    )

    for card in cards:
        # ვეძებთ სათაურს (ჩვეულებრივ h3 ან h4 ან a ტეგი, რომელიც შეიცავს ტექსტს)
        name_el = card.select_one("h3") or card.select_one("h4") or card.select_one("a[href*='/product/']")
        if not name_el:
            continue
            
        name = name_el.get_text(" ", strip=True).strip()
        if len(name) < 2:
            continue

        href_el = card.select_one("a")
        href = href_el.get("href", page_url) if href_el else page_url
        if href.startswith("/"):
            href = f"https://psp.ge{href}"

        # ფასების სელექტორები (ახალ საიტზე ძირითადად ლარის სიმბოლო '₾' უწერიათ გვერდით)
        # ვეძებთ ტექსტს, რომელიც შეიცავს ციფრებს და ლარის ნიშანს
        price_elements = card.find_all(string=lambda text: text and "₾" in text)
        
        if not price_elements:
            # თუ სიმბოლო ვერ იპოვა, ძველი მეთოდით ვცადოთ
            price_el = card.select_one("[class*='price']")
            price = parse_price(price_el.get_text(" ", strip=True)) if price_el else None
        else:
            # თუ იპოვა ტექსტები, პირველი არის მიმდინარე ფასი, მეორე (თუ არსებობს) — ძველი
            prices = [parse_price(p) for p in price_elements if parse_price(p) is not None]
            price = prices[0] if prices else None

        if price is None:
            continue

        old_price = prices[1] if len(prices) > 1 else None
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
            COL_SOURCE:    "PSP",
            COL_URL:       href,
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
        # აუცილებელია ანტი-ბოტისთვის: რეალური იუზერის გარემოს სიმულაცია
        browser = p.chromium.launch(
            headless=True, 
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled" # მალავს რომ ბოტია
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="ka-GE",
        )
        
        page = context.new_page()
        
        # ⚠️ ყურადღება: სურათების ბლოკირება (page.route) წავშალეთ! 
        # Cloudflare ბლოკავს როცა ხედავს, რომ ბრაუზერი სურათების ურლ-ებს აუქმებს.

        for pg in range(1, max_pages + 1):
            # ახალ საიტებზე პაგინაცია ხშირად არის ?page=2 და არა ?p=2
            url = PSP_CATEGORY_URL if pg == 1 else f"{PSP_CATEGORY_URL}?page={pg}"
            if "?p=" in PSP_CATEGORY_URL: # ყოველი შემთხვევისთვის
                url = PSP_CATEGORY_URL if pg == 1 else f"{PSP_CATEGORY_URL}&page={pg}"

            try:
                # ველოდებით სანამ DOM სრულად ჩაიტვირთება
                page.goto(url, wait_until="domcontentloaded", timeout=PW_TIMEOUT)
                # ვაძლევთ რეალურ დროს JS-ს სკრიპტების გასაშვებად
                page.wait_for_timeout(3000) 
                
                # ნელი სქროლი ქვევით, რომ "Lazy loading" პროდუქტები გამოჩნდეს
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/2);")
                page.wait_for_timeout(1000)
            except Exception:
                break

            soup = BeautifulSoup(page.content(), "lxml")
            page_records = _parse_psp_soup(soup, url)

            if not page_records:
                # თუ პირველ გვერდზევე ვერაფერი იპოვა, სცადეთ ალტერნატიული მოლოდინი
                page.wait_for_timeout(2000)
                soup = BeautifulSoup(page.content(), "lxml")
                page_records = _parse_psp_soup(soup, url)
                if not page_records:
                    break

            results.extend(page_records)
            time.sleep(random.uniform(1.5, 3.0)) # უფრო ბუნებრივი დაყოვნება

        browser.close()

    return results
