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
)

def scrape_aversi(max_pages: int) -> list[dict]:
    """
    ავერსის მონაცემების წამოღება შიდა საძიებო API-დან (DevTools-ის ანალოგი).
    ეს მეთოდი მუშაობს პირდაპირ Streamlit Cloud-ზე Cloudflare-ის გვერდის ავლით.
    """
    rows: list[dict] = []
    
    # 🎯 ავერსის ნამდვილი backend API მისამართი, რომელსაც DevTools-ში ხედავდით
    api_url = "https://aversi.ge"
    
    session = requests.Session()
    # ბრაუზერის სრული იმიტაცია, რათა API-მ მოთხოვნა ჩვეულებრივ მომხმარებლად აღიქვას
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ka-GE,ka;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://aversi.ge",
        "Origin": "https://aversi.ge",
        "X-Requested-With": "XMLHttpRequest"
    })

    # გადავუყვებით გვერდებს ციკლით
    for page in range(1, max_pages + 1):
        try:
            # ზუსტი პარამეტრები, რომლებსაც საიტი ფონურად აგზავნის
            params = {
                "category_id": "baby-food",
                "page": page,
                "per_page": 24
            }
            
            resp = session.get(api_url, params=params, timeout=30)
            
            if resp.status_code != 200:
                break
                
            data = resp.json()
            # API-დან წამოღებული პროდუქტების სია
            products = data.get("data", [])
            
            if not products:
                break
                
            for item in products:
                name = item.get("name", "").strip()
                final_price = item.get("price")
                
                if not name or final_price is None:
                    continue
                    
                # ავაწყოთ პროდუქტის დინამიური ბმული
                slug = item.get("slug", "")
                product_url = f"https://aversi.ge/ka/product/{slug}" if slug else "https://aversi.ge/"
                
                row = {
                    COL_NAME: name[:200],
                    COL_PRICE: float(final_price),
                    COL_SOURCE: "Aversi",
                    COL_CATEGORY: CATEGORY_LABEL,
                    COL_URL: product_url,
                    COL_SKU: str(item.get("id", "")),
                }
                
                # ფასდაკლებისა და ძველი ფასის შემოწმება
                old_price = item.get("old_price")
                if old_price and float(old_price) > float(final_price):
                    row[COL_OLD_PRICE] = float(old_price)
                    
                rows.append(row)
                
        except Exception:
            # ხარვეზის შემთხვევაში ვაგრძელებთ მომდევნო გვერდზე, რომ კოდი არ გაჩერდეს
            continue
            
    return rows
