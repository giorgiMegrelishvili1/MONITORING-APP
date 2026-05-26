from __future__ import annotations

import re
import requests
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
)
from common import paginate, sleep_between


def _fetch_html(url: str) -> str:
    """
    ავერსის ბლოკირების ასავლელი ფუნქცია Requests-ით და მოწინავე ბრაუზერის Headers-ით.
    """
    session = requests.Session()
    
    # გაძლიერებული ბრაუზერის იმიტაცია, რომელსაც Cloudflare მარტივად ვერ ბლოკავს
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ka-GE,ka;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    })
    
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


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


def scrape_aversi(max_pages: int) -> list[dict]:
    try:
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
    except Exception:
        # თუ მაინც დაიბლოკა, აბრუნებს ცარიელ სიას, რომ მთლიანი საიტი არ გაითიშოს
        return []
