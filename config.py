# ============================================================
# config.py  — ცენტრალიზებული კონფიგურაცია
# ============================================================

# ── URL-ები ─────────────────────────────────────────────────
PSP_CATEGORY_URL = (
    "https://psp.ge/%E1%83%93%E1%83%94%E1%83%93%E1%83%90-%E1%83%93%E1%83%90-"
    "%E1%83%91%E1%83%90%E1%83%95%E1%83%A8%E1%83%95%E1%83%98/"
    "%E1%83%91%E1%83%90%E1%83%95%E1%83%A8%E1%83%95%E1%83%98%E1%83%A1-"
    "%E1%83%99%E1%83%95%E1%83%94%E1%83%91%E1%83%90.html"
)

AVERSI_LIST_URL = "https://shop.aversi.ge/ka/care-products/baby-food/"

GPC_LIST_URL = "https://gpc.ge/ka/category/baby-food?category=4"

# ── გვერდების ლიმიტი ────────────────────────────────────────
MAX_PAGES_PSP    = 30
MAX_PAGES_AVERSI = 30
MAX_PAGES_GPC    = 30

# ── სვეტების სახელები ───────────────────────────────────────
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
    "Referer": "https://google.com/",
}

# ── Playwright timeout (ms) ──────────────────────────────────
PW_TIMEOUT = 30_000
PW_WAIT_MS = 2_000

# ── ცნობილი ბრენდები კატეგორიზაციისთვის ────────────────────
KNOWN_BRANDS = [
    "HiPP", "Hipp", "hipp",
    "Semper", "semper",
    "NAN", "Nan",
    "Nutrilon", "nutrilon",
    "Similac", "similac",
    "Gerber", "gerber",
    "Heinz", "heinz",
    "Cerelac", "cerelac",
    "FrutoNanny", "Frutonanny",
    "Nestlé", "Nestle",
    "Danone", "danone",
    "Bebelac", "bebelac",
    "Aptamil", "aptamil",
    "Bebiko", "bebiko",
    "Humana", "humana",
    "Milupa", "milupa",
]

# ── ქვეკატეგორიის საკვანძო სიტყვები ────────────────────────
SUBCATEGORY_KEYWORDS = {
    "რძის ნაზავი":  ["ნაზავი", "mixture", "formula", "milk", "infaprim", "nan", "nutrilon", "similac", "aptamil", "bebelac", "humana", "milupa", "bebiko", "hipp 1", "hipp 2", "hipp 3"],
    "ფაფა":         ["ფაფა", "porridge", "cereal", "oat", "wheat", "rice", "semolina", "cerelac", "heinz"],
    "პიურე":        ["პიურე", "puree", "puré", "mashed", "apple", "ვაშლი", "მსხალი", "pear", "banana", "ბანანი"],
    "ჩაი / წყალი":  ["ჩაი", "tea", "water", "წყალი", "herbal"],
    "წვენი":        ["წვენი", "juice", "nectar"],
    "ორცხობილა":    ["ორცხობილა", "biscuit", "cookie", "cracker", "wafer"],
    "დესერტი":      ["დესერტი", "dessert", "yogurt", "pudding", "curd", "ხაჭო"],
    "მზა კვება":    ["spaghetti", "pasta", "soup", "stew", "meat", "vegetable", "dinner", "meal"],
}
