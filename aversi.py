from __future__ import annotations

import re

from bs4 import BeautifulSoup

from config import (
    AVERSI_LIST_URL,
    AVERSI_PAGE_PATTERN,
    CATEGORY_LABEL,
    COL_CATEGORY,
    COL_NAME,
    COL_OLD_PRICE,
    COL_PRICE,
    COL_SKU,
    COL_SOURCE,
    COL_URL,
    HEADERS,
)
# 🔥 გასწორდა: წაიშალა scrapers. პრეფიქსი
from common import get_session, paginate, sleep_between


def _is_cloudflare(html: str) -> bool:
    return "Just a moment" in html or "cf-browser-verification" in html


def _fetch_html(url: str) -> str:
    session = get_session()
    resp = session.get(url, timeout=45)
    resp.raise_for_status()
    text = resp.text
    if _is_cloudflare(text):
        return _fetch_html_playwright(url)
    return text


def _fetch_html_playwright(url: str) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Aversi: Cloudflare დაბლოკავს requests-ს. დააყენეთ: pip install playwright && playwright install chromium"
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(extra_http_headers=HEADERS)
        page.goto(url, wait_until="networkidle", timeout=90000)
        html = page.content()
        browser.close()
    return html


def _page_url(page: int) -> str:
    if page <= 1:
        return AVERSI_LIST_URL
    return AVERSI_PAGE_PATTERN.format(page=page)


def _parse_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict] = []

    for item in soup.select(".ty-grid-list__item"):
        link = item.select_one("a.product-title")
        if not link:
            continue
        name = link.get_text(strip=True)
        href = link.get("href") or ""
        if not name or not href:
            continue

        product_id = ""
        hidden = item.select_one('input[name*="[product_id]"]')
        if hidden and hidden.get("value"):
            product_id = hidden["value"]

        price_nums = item.select("span.ty-price-num")
        prices = []
        for el in price_nums:
            t = el.get_text(strip=True).replace(",", ".")
            if re.fullmatch(r"\d+(\.\d+)?", t):
                prices.append(float(t))
        if not prices:
            continue
        final = prices[0]
        old = None
        old_block = item.select_one(".ty-list-price, .ty-strike")
        if old_block:
            m = re.search(r"(\d+[.,]\d{2})", old_block.get_text().replace(",", "."))
            if m:
                candidate = float(m.group(1))
                if candidate > final:
                    old = candidate

        row = {
            COL_NAME: name[:200],
            COL_PRICE: final,
            COL_SOURCE: "Aversi",
            COL_CATEGORY: CATEGORY_LABEL,
            COL_URL: href,
            COL_SKU: product_id,
        }
        if old:
            row[COL_OLD_PRICE] = old
        rows.append(row)
    return rows


def _detect_last_page(html: str) -> int:
    pages = [int(m.group(1)) for m in re.finditer(r"page-(\d+)", html)]
    return max(pages) if pages else 1


# 🔥 გასწორდა: მოიხსნა ვარსკვლავი (*), რათა პოზიციური არგუმენტი app.py-დან სწორად შემოვიდეს
def scrape_aversi(max_pages: int) -> list[dict]:
    first_html = _fetch_html(AVERSI_LIST_URL)
    last = min(_detect_last_page(first_html), max_pages)

    def fetch_page(page: int) -> list[dict]:
        if page > last:
            return []
        url = _page_url(page)
        html = first_html if page == 1 else _fetch_html(url)
        return _parse_html(html)

    rows = paginate(fetch_page, max_pages=last, stop_on_empty=True)
    sleep_between()
    return rows
