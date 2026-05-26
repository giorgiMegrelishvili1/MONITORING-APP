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

    # ახალ საიტზე ვეძებთ ყველა იმ ელემენტს, რომელიც შეიცავს ლარის სიმბოლოს " ₾"
    price_tags = soup.find_all(string=lambda text: text and " ₾" in text)

    for price_tag in price_tags:
        price_container = price_tag.parent
        if not price_container:
            continue
            
        # ვპოულობთ პროდუქტის მთავარ მშობელ კონტეინერს (Div-ს)
        card = price_container.find_parent("div")
        if not card:
            continue

        # ── სახელი (Name) ──────────────────────────────────
        # ვეძებთ ტექსტს, რომელიც შეიცავს ტირეს ბრენდის გამოსაყოფად (მაგ: "ტირტირი - სახის...")
        name_el = card.find(string=lambda text: text and " - " in text)
        if not name_el:
            # თუ ტირე არ არის, ავიღოთ ბლოკში არსებული პირველი გრძელი ტექსტი, რომელიც ფასი არ არის
            name_elements = [s.strip() for s in card.stripped_strings if len(s.strip()) > 5 and "₾" not in s]
            name = name_elements[0] if name_elements else None
        else:
            name = name_el.strip()

        if not name or len(name) < 2:
            continue

        # დუბლიკატების თავიდან აცილება (რადგან ერთი div შეიძლება რამდენიმე ფასის ტეგს შეიცავდეს)
        if any(r[COL_NAME] == name[:100] for r in records):
            continue

        # ── მიმდინარე ფასი (Current Price) ──────────────────
        price = parse_price(price_tag)
        if price is None:
            continue

        # ── ძველი ფასი (Old Price) ─────────────────────────
        old_price = None
        # ვეძებთ ბლოკში ყველა სხვა ტექსტს, სადაც არის "₾" ნიშანი
        all_prices = card.find_all(string=lambda text: text and "₾" in text)
        for p_str in all_prices:
            if " ₾" not in p_str:  # ახალ ფასს აქვს გამოტოვებული ადგილი " ₾", ძველს კი მიწებებული "5.95₾"
                parsed_old = parse_price(p_str)
                if parsed_old and parsed_old > price:
                    old_price = parsed_old
                    break

        # ── ლინკი (URL) ─────────────────────────────────────
        link_el = card.select_one("a[href*='product']") or card.select_one("a[href*='medicament']") or card.select_one("a[href]")
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
            break   # გვერდები ამოიწურა, ახალი მონაცემები აღარ არის

        results.extend(page_records)
        time.sleep(random.uniform(0.4, 0.9))

    return results
