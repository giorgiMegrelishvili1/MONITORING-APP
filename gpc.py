from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

from bs4 import BeautifulSoup

from config import (
    CATEGORY_LABEL,
    COL_CATEGORY,
    COL_NAME,
    COL_OLD_PRICE,
    COL_PRICE,
    COL_SKU,
    COL_SOURCE,
    COL_URL,
    GPC_LIST_URL,
    GPC_PER_PAGE,
)
# 🔥 გასწორდა: წაიშალა scrapers. პრეფიქსი
from common import get_session, paginate, sleep_between

GPC_BASE = "https://gpc.ge"


def _page_url(base: str, page: int) -> str:
    parsed = urlparse(base)
    qs = parse_qs(parsed.query)
    qs["page"] = [str(page)]
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def _parse_price_block(card) -> tuple[float | None, float | None]:
    """აბრუნებს (ფინალური, ძველი) ფასს."""
    final_el = card.select_one("div[content]")
    if not final_el:
        final_el = card.select_one("div.flex.items-center")
    final = None
    if final_el:
        content = final_el.get("content")
        if content:
            try:
                final = float(content)
            except ValueError:
                pass
        if final is None:
            text = final_el.get_text(" ", strip=True).replace("₾", "").strip()
            m = re.search(r"(\d+[.,]\d{2})", text.replace(",", "."))
            if m:
                final = float(m.group(1).replace(",", "."))
    old = None
    strike = card.select_one(".line-through, .ty-strike, [class*='line-through']")
    if strike:
        m = re.search(r"(\d+[.,]\d{2})", strike.get_text().replace(",", "."))
        if m:
            old = float(m.group(1))
    return final, old


def _parse_html(html: str, page_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    rows: list[dict] = []

    for a in soup.select('a[href*="/ka/details/baby-food"][href*="product="]'):
        href = a.get("href") or ""
        if href in seen:
            continue
        seen.add(href)
        product_id = ""
        m = re.search(r"product=(\d+)", href)
        if m:
            product_id = m.group(1)

        name = ""
        img = a.select_one("img[alt]")
        if img and img.get("alt"):
            name = img["alt"].strip()
        if not name:
            name = a.get_text(" ", strip=True)
        if not name or len(name) < 3:
            continue

        card = a
        for _ in range(6):
            if card.parent and card.parent.name != "body":
                card = card.parent
            else:
                break
        final, old = _parse_price_block(card)
        if final is None:
            continue

        row = {
            COL_NAME: name[:200],
            COL_PRICE: final,
            COL_SOURCE: "GEPHA/GPC",
            COL_CATEGORY: CATEGORY_LABEL,
            COL_URL: urljoin(GPC_BASE, href),
            COL_SKU: product_id,
        }
        if old and old > final:
            row[COL_OLD_PRICE] = old
        rows.append(row)
    return rows


# 🔥 გასწორდა: მოიხსნა ვარსკვლავი (*), რათა app.py-დან გადმოცემული არგუმენტები სწორად წაიკითხოს
def scrape_gpc(max_pages: int, list_url: str = GPC_LIST_URL) -> list[dict]:
    session = get_session()
    session.headers["Referer"] = GPC_BASE

    def fetch_page(page: int) -> list[dict]:
        url = _page_url(list_url, page)
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        rows = _parse_html(resp.text, url)
        if page == 1 and not rows:
            return []
        if len(rows) < 3 and page > 1:
            return []
        return rows

    rows = paginate(fetch_page, max_pages=max_pages, stop_on_empty=True)
    sleep_between()
    return rows
