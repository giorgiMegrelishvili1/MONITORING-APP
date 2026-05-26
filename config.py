# ============================================================
# config.py  — ცენტრალიზებული კონფიგურაცია (Pro-Level)
# ============================================================
from __future__ import annotations

# ── URL-ები (Next.js პლატფორმის პირდაპირი კატეგორიები) ───────────
# PSP: ბავშვთა კვების ძირითადი კატეგორია
PSP_CATEGORY_URL = "https://psp.ge"

# AVERSI: shop. სუბდომენი გაუქმებულია, გადასულია მთავარ დომენზე
AVERSI_LIST_URL  = "https://aversi.ge"

# GPC: პარამეტრი '&page=' რომ სწორად მიებას gpc.py-ში
GPC_LIST_URL     = "https://gpc.ge"


# ── გვერდების ლიმიტი (სისწრაფისა და სტაბილურობისთვის) ──────────
# 10 გვერდი სრულად ფარავს ბავშვის კვების ასორტიმენტს და იცავს Streamlit Cloud-ს ტაიმაუტისგან
MAX_PAGES_PSP    = 10  
MAX_PAGES_AVERSI = 10
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


# ── HTTP Headers ────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ka-GE,ka;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://google.com",
}


# ── ბრაუზერის პარამეტრები (Playwright) ────────────────────────
PW_TIMEOUT = 45_000  # 45 წამი (იცავს აპლიკაციას უეცარი გათიშვისგან)
PW_WAIT_MS = 3_000   # 3 წამი (მოლოდინი ყოველ გვერდზე JS ენდერისთვის)


# ── ქვეკატეგორიის სემანტიკური საკვანძო სიტყვები ────────────────
SUBCATEGORY_KEYWORDS = {
    "რძის ნაზავი":  ["ნაზავი", "mixture", "formula", "milk", "nan", "nutrilon", "similac", "aptamil", "bebelac", "humana", "milupa", "bebiko", "ჰიპ 1", "ჰიპ 2", "ჰიპ 3"],
    "ფაფა":         ["ფაფა", "porridge", "cereal", "oat", "wheat", "rice", "semolina", "cerelac", "heinz", "ფაფები"],
    "პიურე":        ["პიურე", "puree", "puré", "mashed", "ვაშლი", "მსხალი", "ბანანი", "ხილი", "ბოსტნეული"],
    "ჩაი / წყალი":  ["ჩაი", "tea", "water", "წყალი", "ბავშვის წყალი"],
    "წვენი":        ["წვენი", "juice", "nectar"],
    "ორცხობილა":    ["ორცხობილა", "biscuit", "cookie", "cracker"],
    "დესერტი":      ["დესერტი", "dessert", "yogurt", "პუდინგი", "ხაჭო"],
}
