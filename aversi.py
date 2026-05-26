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
    ავერსის მონაცემების წამოღება შიდა API-ს საშუალებით.
    ეს მეთოდი გვერდს ავლის Cloudflare HTML ბლოკირებას Streamlit Cloud-ზე.
    """
    rows: list[dict] = []
    
    # ავერსის შიდა საძიებო API მისამართი ბავშვის კვებისთვის
    api_url = "https://aversi.ge"
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://aversi.ge"
    })

    # გადავუყვებით გვერდებს მომხმარებლის მიერ არჩეული ლიმიტის მიხედვით
    for page in range(1, max_pages + 1):
        try:
            # პარამეტრები API-სთვის (კატეგორიის ID და გვერდი)
            params = {
                "category_id": "baby-food", # ბავშვის კვების კატეგორია
                "page": page,
                "per_page": 24
            }
            
            resp = session.get(api_url, params=params, timeout=30)
            
            # თუ საიტმა შეცდომა დააბრუნა, გადავიდეს შემდეგ ნაწილზე
            if resp.status_code != 200:
                break
                
            data = resp.json()
            products = data.get("data", [])
            
            # თუ მონაცემები ცარიელია, შევაჩეროთ ციკლი
            if not products:
                break
                
            for item in products:
                name = item.get("name", "").strip()
                final_price = item.get("price")
                
                if not name or final_price is None:
                    continue
                    
                # ავაწყოთ პროდუქტის სრული ბმული
                slug = item.get("slug", "")
                product_url = f"https://aversi.ge{slug}" if slug else "https://aversi.ge"
                
                row = {
                    COL_NAME: name[:200],
                    COL_PRICE: float(final_price),
                    COL_SOURCE: "Aversi",
                    COL_CATEGORY: CATEGORY_LABEL,
                    COL_URL: product_url,
                    COL_SKU: str(item.get("id", "")),
                }
                
                # თუ არსებობს ფასდაკლება და ძველი ფასი
                old_price = item.get("old_price")
                if old_price and float(old_price) > float(final_price):
                    row[COL_OLD_PRICE] = float(old_price)
                    
                rows.append(row)
                
        except Exception:
            # შეცდომის შემთხვევაში ვაგრძელებთ, რომ პროგრამა არ გაითიშოს
            continue
            
    return rows
