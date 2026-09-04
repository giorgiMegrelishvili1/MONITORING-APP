# ============================================================
# aversi.py  — Aversi სქრეიფერი
# Aversi (shop.aversi.ge) აგებულია CS-Cart-ზე და გვერდი მთლიანად
# სერვერის მხარეს რენდერდება — არ სჭირდება ბრაუზერი/Playwright.
# უბრალო requests + BeautifulSoup საკმარისია, რაც გაცილებით
# სწრაფი და საიმედოა Streamlit Cloud-ზე.
# ============================================================
from __future__ import annotations

import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from config import (
    AVERSI_BASE, AVERSI_SUBCATEGORIES, MAX_PAGES_AVERSI,
    HEADERS, HTTP_TIMEOUT,
    COL_NAME, COL_PRICE, COL_OLD_PRICE, COL_DISCOUNT,
    COL_BRAND, COL_CATEGORY, COL_SOURCE, COL_URL, COL_UPDATED, COL_NORM_KEY,
)
from common import (
    parse_price, parse_all_prices, normalize_key,
    extract_brand, classify_subcategory, calc_discount_pct,
)


def _parse_aversi_page(soup: BeautifulSoup, page_url: str, subcat_hint: str) -> list[dict]:
    records: list[dict] = []
    seen_hrefs: set[str] = set()

    # პროდუქტის ბმულებს Aversi-ზე აქვს href, რომელიც შეიცავს ქვეკატეგორიის
    # პათს და თან `title` ატრიბუტში სახელია — ეს ყველაზე საიმედო მარკერია,
    # რადგან CSS კლასების სახელები დროთა განმავლობაში იცვლება.
    candidate_links = soup.select("a[href*='/care-products/baby-food/'][title]")

    for a in candidate_links:
        href = a.get("href", "")
        if not href or href in seen_hrefs:
            continue
        # კატეგორია/გვერდის ლინკები არ გვჭირდება (მხოლოდ კონკრეტული პროდუქტები)
        if "page-" in href or href.rstrip("/").split("/")[-1] in (
            "baby-food", "milk-mixture", "porridge-with-milk", "porridge-without-milk",
            "dinner-vegetable-puree", "fruit-purees-for-babies", "dessert-for-babies",
            "pastry-for-babies", "baby-tea-juice-water",
        ):
            continue

        name = (a.get("title") or a.get_text(" ", strip=True)).strip()
        if not name or len(name) < 2:
            continue

        seen_hrefs.add(href)

        # ვეძებთ ყველაზე ახლო კონტეინერს, სადაც ფასია (მშობელი ელემენტების ასვლა)
        container = a
        prices: list[float] = []
        for _ in range(5):
            container = container.parent
            if container is None:
                break
            text_blob = container.get_text(" ", strip=True)
            if "₾" in text_blob:
                prices = parse_all_prices(text_blob)
                if prices:
                    break

        if not prices:
            continue

        price = min(prices)          # ფასდაკლების დროს პატარაა მიმდინარე ფასი
        old_price = max(prices) if len(prices) > 1 and max(prices) > price else None

        full_href = href if href.startswith("http") else f"https://shop.aversi.ge{href}"

        records.append({
            COL_NAME:      name[:100],
            COL_PRICE:     price,
            COL_OLD_PRICE: old_price,
            COL_DISCOUNT:  calc_discount_pct(old_price, price),
            COL_BRAND:     extract_brand(name),
            COL_CATEGORY:  classify_subcategory(name, hint=subcat_hint),
            COL_SOURCE:    "Aversi",
            COL_URL:       full_href,
            COL_NORM_KEY:  normalize_key(name),
            COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    return records


def scrape_aversi(max_pages: int = MAX_PAGES_AVERSI) -> list[dict]:
    """
    Aversi-ს ბავშვის კვების ყველა ქვეკატეგორიის გვერდვის (requests-ით).
    """
    results: list[dict] = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for subcat_label, slug in AVERSI_SUBCATEGORIES:
        base_url = f"{AVERSI_BASE}/{slug}/"

        for pg in range(1, max_pages + 1):
            url = base_url if pg == 1 else f"{base_url}page-{pg}/"

            try:
                resp = session.get(url, timeout=HTTP_TIMEOUT)
                if resp.status_code != 200:
                    break
            except Exception:
                break

            soup = BeautifulSoup(resp.text, "lxml")
            page_records = _parse_aversi_page(soup, url, subcat_label)

            if not page_records:
                break  # აღარ არის მეტი გვერდი ამ ქვეკატეგორიაში

            results.extend(page_records)

            # თუ გვერდზე ცოტა პროდუქტია, სავარაუდოდ ბოლო გვერდია
            if len(page_records) < 5:
                break

            time.sleep(random.uniform(0.4, 0.9))

        time.sleep(random.uniform(0.3, 0.6))

    return results
