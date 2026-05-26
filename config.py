"""წყაროების კონფიგურაცია — URL-ები და პარამეტრები."""

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ka-GE,ka;q=0.9,en;q=0.8",
}

# PSP — Magento GraphQL (ბავშვის კვება, category_id=863)
PSP_GRAPHQL_URL = "https://app.psp.ge/graphql"
PSP_CATEGORY_ID = "863"
PSP_CATEGORY_URL = (
    "https://psp.ge/%E1%83%93%E1%83%94%E1%83%93%E1%83%90-%E1%83%93%E1%83%90-"
    "%E1%83%91%E1%83%90%E1%83%95%E1%83%A8%E1%83%95%E1%83%98/%E1%83%91%E1%83%90%E1%83%95"
    "%E1%83%A8%E1%83%95%E1%83%98%E1%83%A1-%E1%83%99%E1%83%95%E1%83%94%E1%83%91%E1%83%90.html"
)
PSP_PAGE_SIZE = 48  # სწრაფი ჩატვირთვისთვის (სულ ~684 პროდუქტი ≈ 15 გვერდი)

# GPC / GEPHA — Next.js SSR HTML
GPC_LIST_URL = "https://gpc.ge/ka/category/baby-food?category=4"
GPC_PER_PAGE = 24

# Aversi — CS-Cart (Cloudflare-ზე შეიძლება დაგჭირდეთ Playwright)
AVERSI_LIST_URL = "https://shop.aversi.ge/ka/care-products/baby-food/"
AVERSI_PAGE_PATTERN = "https://shop.aversi.ge/ka/care-products/baby-food/page-{page}/"

# სკრეიპინგის ლიმიტები (რეალურ დროში — ყველა გვერდი ძალიან ნელია)
MAX_PAGES_PSP = 50
MAX_PAGES_GPC = 50
MAX_PAGES_AVERSI = 30
REQUEST_DELAY_SEC = 0.35

# ერთიანი სვეტები
COL_NAME = "სახელი"
COL_PRICE = "ფასი (₾)"
COL_OLD_PRICE = "ძველი ფასი (₾)"
COL_SOURCE = "წყარო"
COL_CATEGORY = "კატეგორია"
COL_URL = "URL"
COL_SKU = "SKU"
COL_UPDATED = "განახლდა"

CATEGORY_LABEL = "ბავშვის კვება"
