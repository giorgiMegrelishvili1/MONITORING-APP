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
    ზუსტად კითხულობს ფასს მხოლოდ ფასის კონკრეტული ელემენტებიდან.
    სრულად გამორიცხავს პროდუქტის სახელში არსებულ ციფრებს (მაგ. 3, 12თვ+).
    """
    final = None
    old = None
    
    # GPC-ზე რეალური ფასი თითქმის ყოველთვის დევს 'div[content]' ატრიბუტში
    final_el = card.select_one("div[content]")
    if final_el and final_el.get("content"):
        try:
            final = float(final_el["content"])
        except ValueError:
            pass
            
    # თუ content ატრიბუტი არ დაგვხვდა, ფასს ვეძებთ სპეციალურ ფასის კონტეინერში
    if final is None:
        price_container = card.select_one("[class*='price'], [class*='Price']")
        if price_container:
            clean_text = price_container.get_text(" ", strip=True).replace("₾", "").strip()
            clean_text = re.sub(r"-\d+(?:[.,]\d+)?%", "", clean_text)
            nums = [float(m.replace(",", ".")) for m in re.findall(r"(\d+(?:[.,]\d+)?)", clean_text)]
            if nums:
                final = nums[0]
                if len(nums) >= 2 and nums[1] > nums[0]:
                    old = nums[1]

    # ცალკე ვეძებთ ხაზგადასმულ ძველ ფასს
    strike = card.select_one(".line-through, .ty-strike, [class*='line-through']")
    if strike and old is None: # 🔥 გასწორდა: წაიშალა შეცდომით ჩაწერილი სიტყვა
        strike_text = strike.get_text(" ", strip=True).replace("₾", "").replace(",", ".").strip()
        m_old = re.search(r"(\d+(?:[.,]\d+)?)", strike_text)
        if m_old:
            candidate_old = float(m_old.group(1))
            if final and candidate_old > final:
                old = candidate_old
                
    return final, old


def _parse_html(html: str, page_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    rows: list[dict] = []

    # ვპოულობთ პროდუქტის ბარათებს
    for card in soup.select("div:has(> a[href*='product=']), [class*='product-item'], div:has(> [class*='cart'])"):
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
            name = a.get_text(" ", strip=True)
            
        if not name or len(name) < 3:
            continue

        # ფასების წაკითხვა დაზუსტებული ბლოკიდან
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
