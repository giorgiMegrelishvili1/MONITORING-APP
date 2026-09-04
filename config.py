# ============================================================
# config.py  — ცენტრალიზებული კონფიგურაცია (Pro-Level, v2)
# ============================================================
from __future__ import annotations

# ── PSP ──────────────────────────────────────────────────────
# რეალური კატეგორიის გვერდი (ადრე მთავარ გვერდზე იყო მითითებული — ეს იყო
# სქრეიფინგის ჩავარდნის მთავარი მიზეზი, რადგან მთავარ გვერდზე პროდუქტები არაა)
PSP_CATEGORY_URL = "https://psp.ge/დედა-და-ბავშვი/ბავშვის-კვება.html"

# ── Aversi (CS-Cart, სერვერზე რენდერდება — Playwright არაა საჭირო) ─────
# Aversi-ზე ბავშვის კვება დაყოფილია ქვეკატეგორიებად და თითოეულს თავისი
# გვერდი აქვს (არა ერთი საერთო სია). (label, url_slug)
AVERSI_BASE = "https://shop.aversi.ge/ka/care-products/baby-food"
AVERSI_SUBCATEGORIES = [
    ("რძის ნაზავი",     "milk-mixture"),
    ("რძიანი ფაფა",      "porridge-with-milk"),
    ("ურძეო ფაფა",       "porridge-without-milk"),
    ("პიურე",            "dinner-vegetable-puree"),
    ("ხილფაფა",          "fruit-purees-for-babies"),
    ("დესერტი",          "dessert-for-babies"),
    ("ორცხობილა",        "pastry-for-babies"),
    ("ჩაი / წყალი",      "baby-tea-juice-water"),
]

# ── GPC (Next.js, სერვერზე რენდერდება — Playwright არაა საჭირო) ────────
GPC_LIST_URL = "https://gpc.ge/en/category/baby-food"
GPC_CATEGORY_ID = "4"

# ── გვერდების ლიმიტი (სისწრაფისა და სტაბილურობისთვის) ──────────
MAX_PAGES_PSP    = 8
MAX_PAGES_AVERSI = 6   # თითო ქვეკატეგორიაზე
MAX_PAGES_GPC    = 10

# ── სვეტების სახელები ბაზაში ─────────────────────────────────
COL_NAME      = "სახელი"
COL_PRICE     = "ფასი"
COL_OLD_PRICE = "ძველი_ფასი"
COL_DISCOUNT  = "ფასდაკლება_%"
COL_BRAND     = "ბრენდი"
COL_CATEGORY  = "კატეგორია"
COL_SOURCE    = "წყარო"
COL_URL       = "URL"
COL_UPDATED   = "განახლდა"
COL_NORM_KEY  = "norm_key"

# ── HTTP Headers (requests-სქრეიფერებისთვის: Aversi, GPC) ──────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ka-GE,ka;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

HTTP_TIMEOUT = 20  # წამი, requests-ისთვის

# ── ბრაუზერის პარამეტრები (Playwright — მხოლოდ PSP-სთვის) ──────
PW_TIMEOUT = 45_000
PW_WAIT_MS = 3_000

# ── ქვეკატეგორიის სემანტიკური საკვანძო სიტყვები ────────────────
SUBCATEGORY_KEYWORDS = {
    "რძის ნაზავი":  ["ნაზავი", "mixture", "formula", "milk", "nan", "nutrilon", "similac", "aptamil", "bebelac", "humana", "milupa", "bebiko", "ჰიპ 1", "ჰიპ 2", "ჰიპ 3", "mamako", "friso", "hipp"],
    "ფაფა":         ["ფაფა", "porridge", "cereal", "oat", "wheat", "rice", "semolina", "cerelac", "heinz", "ფაფები"],
    "პიურე":        ["პიურე", "puree", "puré", "mashed", "ვაშლი", "მსხალი", "ბანანი", "ხილი", "ბოსტნეული", "pouch"],
    "ჩაი / წყალი":  ["ჩაი", "tea", "water", "წყალი", "ბავშვის წყალი"],
    "წვენი":        ["წვენი", "juice", "nectar"],
    "ორცხობილა":    ["ორცხობილა", "biscuit", "cookie", "cracker"],
    "დესერტი":      ["დესერტი", "dessert", "yogurt", "პუდინგი", "ხაჭო"],
}

# 💡 სათადარიგო ცარიელი მასივი იმპორტის შეცდომების დასაზღვევად
KNOWN_BRANDS = [
    "Hipp", "Nan", "Nutrilon", "Similac", "Aptamil", "Humana", "Heinz", "Cerelac",
    "Semper", "Frutonanny", "Gerber", "Mamako", "Friso", "Nutrilak", "Kabrita",
    "Baia", "Hero Baby", "Vinni", "Plasmon", "Milyn Paras", "Babybio", "Pico",
]

