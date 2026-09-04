# ============================================================
# gpc.py  — GPC (gpc.ge) სქრეიფერი
# GPC აგებულია Next.js-ზე, მაგრამ პროდუქტების სია სერვერის მხარეს
# წინასწარ არის რენდერილი (SSR) — უბრალო requests საკმარისია,
# ბრაუზერი/Playwright არ სჭირდება.
# ============================================================
from __future__ import annotations

import re
import json
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from config import (
    GPC_LIST_URL, GPC_CATEGORY_ID, MAX_PAGES_GPC,
    HEADERS, HTTP_TIMEOUT,
    COL_NAME, COL_PRICE, COL_OLD_PRICE, COL_DISCOUNT,
    COL_BRAND, COL_CATEGORY, COL_SOURCE, COL_URL, COL_UPDATED, COL_NORM_KEY,
)
from common import (
    parse_price, parse_all_prices, normalize_key, extract_brand,
    classify_subcategory, calc_discount_pct, find_product_lists, get_field,
)


def _record_from_json_product(prod: dict, page_url: str) -> dict | None:
    name = get_field(prod, {"name", "title", "productname", "product_name"})
    price = get_field(prod, {"price", "currentprice", "current_price", "salesprice", "sales_price"})
    if not name or price in (None, ""):
        return None
    try:
        price = float(str(price).replace(",", "."))
    except (TypeError, ValueError):
        return None

    old_price_raw = get_field(prod, {"oldprice", "old_price", "regularprice", "regular_price"})
    old_price = None
    if old_price_raw not in (None, ""):
        try:
            old_price = float(str(old_price_raw).replace(",", "."))
        except (TypeError, ValueError):
            old_price = None

    slug = get_field(prod, {"slug", "url", "urlkey", "url_key"})
    pid = get_field(prod, {"id", "productid", "product_id"})
    href = f"https://gpc.ge/en/details/{slug}?product={pid}" if slug else page_url

    return {
        COL_NAME:      str(name)[:100],
        COL_PRICE:     price,
        COL_OLD_PRICE: old_price if (old_price and old_price > price) else None,
        COL_DISCOUNT:  calc_discount_pct(old_price, price),
        COL_BRAND:     extract_brand(str(name)),
        COL_CATEGORY:  classify_subcategory(str(name)),
        COL_SOURCE:    "GPC",
        COL_URL:       href,
        COL_NORM_KEY:  normalize_key(str(name)),
        COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def _parse_via_next_data(soup: BeautifulSoup, page_url: str) -> list[dict]:
    next_data = soup.find("script", id="__NEXT_DATA__")
    if not next_data or not next_data.string:
        return []
    try:
        data = json.loads(next_data.string)
    except Exception:
        return []

    records = []
    for lst in find_product_lists(data):
        for prod in lst:
            rec = _record_from_json_product(prod, page_url)
            if rec:
                records.append(rec)
    return records


def _parse_via_html(soup: BeautifulSoup, page_url: str) -> list[dict]:
    """
    ალტერნატივა, თუ __NEXT_DATA__-ში ვერ ვიპოვეთ პროდუქტების სია:
    ვეძებთ პროდუქტის დეტალების ბმულებს (href შეიცავს '/details/')
    და მათ გვერდით ფასს ('₾' სიმბოლოთი).
    """
    records = []
    seen = set()
    links = soup.select("a[href*='/details/']")

    for a in links:
        href = a.get("href", "")
        if not href or href in seen:
            continue
        text_blob = a.get_text(" ", strip=True)
        if "₾" not in text_blob:
            continue
        seen.add(href)

        prices = parse_all_prices(text_blob)
        if not prices:
            continue
        price = min(prices)
        old_price = max(prices) if len(prices) > 1 and max(prices) > price else None

        # სახელი — ტექსტიდან ფასის ნაწილის მოცილებით (მიახლოებით)
        name = re.split(r"\d{1,6}(?:[.,]\d{1,2})?\s*₾", text_blob)[0].strip()
        name = re.sub(r"\s{2,}", " ", name).strip(" -")
        if not name or len(name) < 2:
            continue

        full_href = href if href.startswith("http") else f"https://gpc.ge{href}"

        records.append({
            COL_NAME:      name[:100],
            COL_PRICE:     price,
            COL_OLD_PRICE: old_price,
            COL_DISCOUNT:  calc_discount_pct(old_price, price),
            COL_BRAND:     extract_brand(name),
            COL_CATEGORY:  classify_subcategory(name),
            COL_SOURCE:    "GPC",
            COL_URL:       full_href,
            COL_NORM_KEY:  normalize_key(name),
            COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    return records


def scrape_gpc(max_pages: int = MAX_PAGES_GPC) -> list[dict]:
    results: list[dict] = []
    session = requests.Session()
    session.headers.update(HEADERS)

    seen_keys: set[str] = set()

    for pg in range(1, max_pages + 1):
        url = f"{GPC_LIST_URL}?category={GPC_CATEGORY_ID}&page={pg}"
        try:
            resp = session.get(url, timeout=HTTP_TIMEOUT)
            if resp.status_code != 200:
                break
        except Exception:
            break

        soup = BeautifulSoup(resp.text, "lxml")

        page_records = _parse_via_next_data(soup, url)
        if not page_records:
            page_records = _parse_via_html(soup, url)

        if not page_records:
            break

        # დუბლიკატების გაფილტვრა (URL-პარამეტრით პაგინაცია ხანდახან იმეორებს)
        new_records = [r for r in page_records if r[COL_URL] not in seen_keys]
        if not new_records:
            break
        for r in new_records:
            seen_keys.add(r[COL_URL])

        results.extend(new_records)

        if len(page_records) < 5:
            break

        time.sleep(random.uniform(0.4, 0.9))

    return results
