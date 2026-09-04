# ============================================================
# common.py  — საზიარო ფუნქციები (v2)
# ============================================================
from __future__ import annotations

import re
import unicodedata
from config import KNOWN_BRANDS, SUBCATEGORY_KEYWORDS


# ── ფასის პარსინგი ───────────────────────────────────────────
def parse_price(text: str) -> float | None:
    """
    მიწოდებული სტრინგიდან ამოიღებს პირველ ვალიდურ GEL ფასს.
    მხარს უჭერს: '24.80₾', '24,80 GEL', '24.80', '₾ 24.80', '24.80 ₾'
    """
    if not text:
        return None
    cleaned = (
        str(text)
        .replace("\xa0", " ")
        .replace(",", ".")
        .strip()
    )
    m = re.search(r"(\d{1,6}(?:\.\d{1,2})?)", cleaned)
    if m:
        val = float(m.group(1))
        if 0.1 < val < 9_999:   # სანიტარული შემოწმება
            return round(val, 2)
    return None


def parse_all_prices(text: str) -> list[float]:
    """ტექსტში ყველა ფასის (GEL რიცხვის) მოძებნა, თანმიმდევრობით."""
    if not text:
        return []
    cleaned = str(text).replace("\xa0", " ").replace(",", ".")
    vals = []
    for m in re.finditer(r"(\d{1,6}(?:\.\d{1,2})?)\s*₾", cleaned):
        v = float(m.group(1))
        if 0.1 < v < 9_999:
            vals.append(round(v, 2))
    return vals


# ── ნორმალიზებული გასაღები შედარებისთვის ──────────────────
_NOISE = re.compile(
    r"[\s\-_/\\.,;:!?\(\)\[\]\"'`«»""'']+", flags=re.UNICODE
)
_UNITS = re.compile(
    r"\b(\d+\s*(?:გ|მლ|ლ|კგ|g|ml|l|kg|gr|pcs|ც|pack|pk))\b",
    flags=re.IGNORECASE | re.UNICODE,
)


def normalize_key(name: str, keep_volume: bool = True) -> str:
    """
    პროდუქტის სახელიდან ქმნის შედარებად ნორმალიზებულ გასაღებს.
    პრინციპი: brand + numeric_volume → ერთ საიტზე იგივე SKU = ერთი key.
    """
    s = name.lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"\(.*?\)", " ", s)
    s = _NOISE.sub("", s)
    s = re.sub(r"[^\w]", "", s, flags=re.UNICODE)
    if not keep_volume:
        s = _UNITS.sub("", s)
    return s[:30]


# ── ბრენდის ამოღება ─────────────────────────────────────────
def extract_brand(name: str) -> str:
    name_l = name.lower()
    for brand in KNOWN_BRANDS:
        if brand.lower() in name_l:
            return brand
    return name.split()[0].capitalize() if name.split() else "სხვა"


# ── ქვეკატეგორიის განსაზღვრა ────────────────────────────────
def classify_subcategory(name: str, hint: str | None = None) -> str:
    """
    hint — თუ სქრეიფერმა უკვე იცის ქვეკატეგორია საიტის სტრუქტურიდან
    (მაგ. Aversi-ს URL-ის მიხედვით), ჯერ მას ვცდილობთ.
    """
    if hint and hint in SUBCATEGORY_KEYWORDS:
        return hint
    name_l = name.lower()
    for subcat, keywords in SUBCATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in name_l:
                return subcat
    return hint or "სხვა"


# ── ფასდაკლების % გამოთვლა ──────────────────────────────────
def calc_discount_pct(old: float | None, new: float | None) -> float | None:
    if old and new and old > new > 0:
        return round((old - new) / old * 100, 1)
    return None


# ── გენერული JSON "პროდუქტების სია" ამომცნობი ──────────────
# გამოსადეგია Next.js/React საიტებზე ჩაშენებული __NEXT_DATA__ JSON-ის
# დასამუშავებლად, როცა ზუსტი key-გზა წინასწარ უცნობია.
_PRICE_KEYS = {"price", "currentprice", "current_price", "salesprice", "sales_price"}
_NAME_KEYS = {"name", "title", "productname", "product_name"}


def find_product_lists(obj, _depth: int = 0) -> list[list[dict]]:
    """
    რეკურსიულად დადის JSON სტრუქტურაში და აბრუნებს ყველა სიას,
    რომლის ელემენტებიც წააგავს პროდუქტის ობიექტებს (აქვთ სახელი + ფასი).
    """
    found: list[list[dict]] = []
    if _depth > 12:
        return found

    if isinstance(obj, list):
        if obj and all(isinstance(el, dict) for el in obj):
            sample_keys = {k.lower() for el in obj[:5] for k in el.keys()}
            if (sample_keys & _NAME_KEYS) and (sample_keys & _PRICE_KEYS):
                found.append(obj)
        for el in obj:
            found.extend(find_product_lists(el, _depth + 1))

    elif isinstance(obj, dict):
        for v in obj.values():
            found.extend(find_product_lists(v, _depth + 1))

    return found


def get_field(d: dict, keys: set[str]):
    for k, v in d.items():
        if k.lower() in keys and v not in (None, ""):
            return v
    return None
