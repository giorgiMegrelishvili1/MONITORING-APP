from __future__ import annotations

import requests

from config import (
    CATEGORY_LABEL,
    COL_CATEGORY,
    COL_NAME,
    COL_OLD_PRICE,
    COL_PRICE,
    COL_SKU,
    COL_SOURCE,
    COL_URL,
    PSP_CATEGORY_ID,
    PSP_CATEGORY_URL,
    PSP_GRAPHQL_URL,
    PSP_PAGE_SIZE,
)
from common import get_session, paginate, sleep_between

# GraphQL მოთხოვნა პროდუქტებისა და ფასების სტრუქტურის მისაღებად
PSP_PRODUCTS_QUERY = """
query products(
  $currentPage: Int = 1
  $pageSize: Int = 20
  $filter: ProductAttributeFilterInput
) {
  products(
    currentPage: $currentPage
    pageSize: $pageSize
    filter: $filter
  ) {
    total_count
    page_info {
      current_page
      total_pages
    }
    items {
      sku
      name
      url_rewrites { url }
      price_range {
        maximum_price {
          final_price { value }
          regular_price { value }
        }
      }
    }
  }
}
"""


def _parse_item(item: dict) -> dict | None:
    name = (item.get("name") or "").strip()
    if not name:
        return None
        
    # უსაფრთხოდ მივყვებით ფასების იერარქიას
    price_range = item.get("price_range", {})
    max_price = price_range.get("maximum_price", {}) if price_range else {}
    
    final = max_price.get("final_price", {}).get("value")
    regular = max_price.get("regular_price", {}).get("value")
    
    if final is None:
        return None
        
    # უსაფრთხოდ ამოვაარქივოთ პროდუქტის URL მისამართი
    url_path = ""
    rewrites = item.get("url_rewrites")
    if rewrites and isinstance(rewrites, list) and len(rewrites) > 0:
        url_path = rewrites[0].get("url") or ""
    elif isinstance(rewrites, dict):
        url_path = rewrites.get("url") or ""
        
    url = f"https://psp.ge/{url_path.lstrip('/')}" if url_path else PSP_CATEGORY_URL
    
    row = {
        COL_NAME: name[:200],
        COL_PRICE: float(final),
        COL_SOURCE: "PSP",
        COL_CATEGORY: CATEGORY_LABEL,
        COL_URL: url,
        COL_SKU: str(item.get("sku") or ""),
    }
    
    # ფასდაკლების (ძველი ფასის) ვალიდაცია
    if regular and float(regular) > float(final):
        row[COL_OLD_PRICE] = float(regular)
        
    return row


def scrape_psp(max_pages: int, page_size: int = PSP_PAGE_SIZE) -> list[dict]:
    session = get_session()
    session.headers["Content-Type"] = "application/json"
    session.headers["Origin"] = "https://psp.ge"
    session.headers["Referer"] = PSP_CATEGORY_URL

    total_pages = 1

    def fetch_page(page: int) -> list[dict]:
        nonlocal total_pages
        if page > total_pages:
            return []
            
        payload = {
            "query": PSP_PRODUCTS_QUERY,
            "variables": {
                "currentPage": page,
                "pageSize": page_size,
                "filter": {"category_id": {"eq": PSP_CATEGORY_ID}},
            },
        }
        
        resp = session.post(PSP_GRAPHQL_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get("errors"):
            return []
            
        products = data.get("data", {}).get("products") or {}
        
        # დინამიურად ვანახლებთ გვერდების რაოდენობას
        total_pages = min(
            int(products.get("page_info", {}).get("total_pages") or 1),
            max_pages,
        )
        
        items = products.get("items") or []
        rows = []
        for item in items:
            row = _parse_item(item)
            if row:
                rows.append(row)
        return rows

    rows = paginate(fetch_page, max_pages=max_pages, stop_on_empty=True)
    sleep_between()
    return rows
