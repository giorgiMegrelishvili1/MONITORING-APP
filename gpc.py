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
from common import get_session, paginate, sleep_between

GPC_BASE = "https://gpc.ge"


def _page_url(base: str, page: int) -> str:
    parsed = urlparse(base)
    qs = parse_qs(parsed.query)
    qs["page"] = [str(page)]
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def _parse_price_block(card) -> tuple[float | None, float | None]:
    """
    ზუსტად კითხულობს ფინალურ და ძველ ფასებს GPC-ის ახალი სტრუქტურიდან.
    სრულად უგულებელყოფს პროცენტებს (-30.0%), რაც ფასების არევას იწვევდა.
    """
    final = None
    old = None
    
    # 1. ვიღებთ ბლოკის სრულ ტექსტს
    text_content = card.get_text(" ", strip=True)
    
    # 2. ვასუფთავებთ ტექსტს პროცენტის ნიშნებისგან, რომ ციფრებში არ შემოგვეპაროს
    text_content = re.sub(r"-\d+(?:[.,]\d+)?%", "", text_content)  # შლის მაგ. "-30.0%"
    text_content = text_content.replace("₾", "").strip()
    
    # 3. ვეძებთ მხოლოდ დარჩენილ რეალურ ფასებს
    prices = [float(m.replace(",", ".")) for m in re.findall(r"(\d+(?:[.,]\d+)?)", text_content)]
    
    # 4. ფასების განაწილება ლოგიკით
    if len(prices) >= 2:
        # პირველი არის ახალი ფასი (მაგ. 7.60), მეორე - ძველი (მაგ. 10.85)
        final = prices[0]
        if prices[1] > prices[0]:
            old = prices[1]
    elif len(prices) == 1:
        final = prices[0]
        
    return final, old


def _parse_html(html: str, page_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    rows: list[dict] = []

    # ახალი სელექტორი, რომელიც პოულობს პროდუქტის ნებისმიერ ბლოკს/ბარათს გვერდზე
    for card in soup.select("div:has(> a[href*='product=']), div:has(> [class*='cart'])"):
        a = card.select_one("a[href*='product=']")
        if not a:
            continue
            
        href = a.get("href") or ""
        if href in seen:
            continue
        seen.add(href)
        
        product_id = ""
        m = re.search(r"product=(\d+)", href)
        if m:
            product_id = m.group(1)

        # სახელის ამოღება უსაფრთხოდ
        name = ""
        img = card.select_one("img[alt]")
        if img and img.get("alt"):
            name = img["alt"].strip()
        if not name:
            name = card.get_text(" ", strip=True).split("₾")[0].strip()
            
        if not name or len(name) < 3:
            continue

        # ფასების წაკითხვა
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
