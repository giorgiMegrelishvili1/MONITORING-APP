python# ============================================================
# app.py  — 🍼 ბავშვის კვება: Pro-Level ფასების ინდექსი
# PSP · Aversi · GPC  |  გაშვება: streamlit run app.py
# ============================================================
from __future__ import annotations

import os, sys, re, traceback
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ── კონფიგი ─────────────────────────────────────────────────
try:
    from config import (
        COL_NAME, COL_PRICE, COL_OLD_PRICE,
        COL_CATEGORY, COL_SOURCE, COL_URL,
        COL_UPDATED,
        MAX_PAGES_PSP, MAX_PAGES_AVERSI, MAX_PAGES_GPC,
    )
    # 🔥 დაზღვევა: ვქმნით ცვლადებს, რადგან config.py-ში არ გაქვთ
    COL_DISCOUNT = "discount"
    COL_BRAND = "brand"
    COL_NORM_KEY = "norm_key"
except Exception:
    st.error("config.py ჩატვირთვა ვერ მოხერხდა")
    st.code(traceback.format_exc()); st.stop()

# ── სქრეიფერები ──────────────────────────────────────────────
try:
    from gpc    import scrape_gpc
    from psp    import scrape_psp
    from aversi import scrape_aversi
    # 🔥 გასწორდა: მოიხსნა classify_subcategory, რადგან common.py-ში არ გაქვთ
    from common import normalize_key
except Exception:
    st.error("სქრეიფერის ფაილი ვერ ჩაიტვირთა")
    st.code(traceback.format_exc()); st.stop()

# ════════════════════════════════════════════════════════════
# PAGE SETUP
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="🍼 ბავშვის კვება · ფასების ინგდექსი",
    page_icon="🍼",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  /* კარდები */
  div[data-testid="metric-container"] {
    background:#fff; border:1px solid #e2e8f0; border-radius:14px;
    padding:16px 20px; box-shadow:0 2px 6px rgba(0,0,0,.06);
  }
  /* ტაბები */
  .stTabs [data-baseweb="tab-list"]{gap:6px}
  .stTabs [data-baseweb="tab"]{border-radius:8px 8px 0 0; padding:8px 18px}
  /* ბეჯები */
  .badge{display:inline-block;padding:3px 11px;border-radius:20px;
         font-size:12px;font-weight:700;margin:1px}
  .b-psp   {background:#e3f2fd;color:#0d47a1}
  .b-aversi{background:#e8f5e9;color:#1b5e20}
  .b-gpc   {background:#fff3e0;color:#bf360c}
  /* სათაური */
  h1{font-size:1.85rem!important}
  .block-container{padding-top:1.2rem}
  /* insight box */
  .insight-box{background:#f0f4ff;border-left:4px solid #3b5bdb;
               border-radius:8px;padding:12px 16px;margin:6px 0;
               font-size:.93rem;line-height:1.55}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# DEMO DATA — რეალური სქრეიფინგის არარსებობისას
# ════════════════════════════════════════════════════════════
DEMO: list[dict] = [
    # ─── რძის ნაზავი ─────────────────────────────────────────
    {COL_NAME:"HiPP Organic 1 (800გ)",     COL_PRICE:89.90,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Hipp",     COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"HiPP Organic 1 (800გ)",     COL_PRICE:92.50,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Hipp",     COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"HiPP Organic 1 (800გ)",     COL_PRICE:88.00,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Hipp",     COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    {COL_NAME:"NAN Optipro 1 (800გ)",       COL_PRICE:72.00,COL_OLD_PRICE:80.00,COL_DISCOUNT:10.0, COL_BRAND:"Nan",      COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"NAN Optipro 1 (800გ)",       COL_PRICE:74.50,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Nan",      COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"NAN Optipro 1 (800გ)",       COL_PRICE:71.00,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Nan",      COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    {COL_NAME:"Nutrilon Premium 1 (400გ)", COL_PRICE:45.00,COL_OLD_PRICE:50.00,COL_DISCOUNT:10.0, COL_BRAND:"Nutrilon", COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"Nutrilon Premium 1 (400გ)", COL_PRICE:46.50,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Nutrilon", COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"Nutrilon Premium 1 (400გ)", COL_PRICE:44.00,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Nutrilon", COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    {COL_NAME:"Similac 1 (400გ)",           COL_PRICE:38.50,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Similac",  COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"Similac 1 (400გ)",           COL_PRICE:39.00,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Similac",  COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    {COL_NAME:"Aptamil 1 (800გ)",           COL_PRICE:95.00,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Aptamil",  COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"Aptamil 1 (800გ)",           COL_PRICE:97.00,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Aptamil",  COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    {COL_NAME:"Humana 1 (600გ)",            COL_PRICE:62.00,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Humana",   COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"Humana 1 (600გ)",            COL_PRICE:60.50,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Humana",   COL_CATEGORY:"რძის ნაზავი",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    # ─── ფაფა ────────────────────────────────────────────────
    {COL_NAME:"Heinz ბრინჯის ფაფა (200გ)", COL_PRICE:9.90, COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Heinz",   COL_CATEGORY:"ფაფა",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"Heinz ბრინჯის ფაფა (200გ)", COL_PRICE:10.20,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Heinz",   COL_CATEGORY:"ფაფა",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"Heinz ბრინჯის ფაფა (200გ)", COL_PRICE:9.50, COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Heinz",   COL_CATEGORY:"ფაფა",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    {COL_NAME:"Cerelac ხორბლის ფაფა (250გ)",COL_PRICE:14.90,COL_OLD_PRICE:17.00,COL_DISCOUNT:12.4,COL_BRAND:"Cerelac", COL_CATEGORY:"ფაფა",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"Cerelac ხორბლის ფაფა (250გ)",COL_PRICE:15.20,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Cerelac", COL_CATEGORY:"ფაფა",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"Cerelac ხორბლის ფაფა (250გ)",COL_PRICE:14.50,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Cerelac", COL_CATEGORY:"ფაფა",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    {COL_NAME:"Semper რძიანი ფაფა (180გ)", COL_PRICE:11.50,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Semper",  COL_CATEGORY:"ფაფა",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"Semper რძიანი ფაფა (180გ)", COL_PRICE:11.80,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Semper",  COL_CATEGORY:"ფაფა",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    {COL_NAME:"HiPP ორგანული ფაფა (200გ)", COL_PRICE:13.90,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Hipp",    COL_CATEGORY:"ფაფა",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"HiPP ორგანული ფაფა (200გ)", COL_PRICE:14.50,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Hipp",    COL_CATEGORY:"ფაფა",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    # ─── პიურე ───────────────────────────────────────────────
    {COL_NAME:"Semper ვაშლი 80გ",          COL_PRICE:3.43, COL_OLD_PRICE:4.90, COL_DISCOUNT:30.0, COL_BRAND:"Semper",  COL_CATEGORY:"პიურე",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    {COL_NAME:"Semper ვაშლი 80გ",          COL_PRICE:3.70, COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Semper",  COL_CATEGORY:"პიურე",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"Semper ვაშლი 80გ",          COL_PRICE:3.55, COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Semper",  COL_CATEGORY:"პიურე",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"FrutoNanny ხაჭოს პიურე 100გ",COL_PRICE:3.95,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Frutonanny",COL_CATEGORY:"პიურე",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"FrutoNanny ხაჭოს პიურე 100გ",COL_PRICE:4.10,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Frutonanny",COL_CATEGORY:"პიურე",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"Gerber მწვანე ბარდა 130გ",  COL_PRICE:4.50, COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Gerber",  COL_CATEGORY:"პიურე",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"Gerber მწვანე ბარდა 130გ",  COL_PRICE:4.70, COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Gerber",  COL_CATEGORY:"პიურე",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"HiPP ვაშლ-მსხლის პიურე",   COL_PRICE:4.80, COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Hipp",    COL_CATEGORY:"პიურე",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    {COL_NAME:"HiPP ვაშლ-მსხლის პიურე",   COL_PRICE:5.00, COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Hipp",    COL_CATEGORY:"პიურე",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    # ─── ორცხობილა ───────────────────────────────────────────
    {COL_NAME:"Semper მარწყვის ორცხობილა 125გ",COL_PRICE:7.90,COL_OLD_PRICE:10.95,COL_DISCOUNT:28.0,COL_BRAND:"Semper",COL_CATEGORY:"ორცხობილა",COL_SOURCE:"GPC",  COL_URL:"https://gpc.ge"},
    {COL_NAME:"Semper მარწყვის ორცხობილა 125გ",COL_PRICE:8.20,COL_OLD_PRICE:None, COL_DISCOUNT:None,COL_BRAND:"Semper",COL_CATEGORY:"ორცხობილა",COL_SOURCE:"PSP",  COL_URL:"https://psp.ge"},
    {COL_NAME:"HiPP ბავშვის ნამცხვარი 150გ",COL_PRICE:9.50,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Hipp",   COL_CATEGORY:"ორცხობილა",COL_SOURCE:"PSP",  COL_URL:"https://psp.ge"},
    {COL_NAME:"HiPP ბავშვის ნამცხვარი 150გ",COL_PRICE:9.80,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Hipp",   COL_CATEGORY:"ორცხობილა",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    # ─── ჩაი / წყალი ─────────────────────────────────────────
    {COL_NAME:"HiPP საბავშვო ჩაი ქამომილა 200მლ",COL_PRICE:6.50,COL_OLD_PRICE:None,COL_DISCOUNT:None,COL_BRAND:"Hipp",COL_CATEGORY:"ჩაი / წყალი",COL_SOURCE:"PSP",  COL_URL:"https://psp.ge"},
    {COL_NAME:"HiPP საბავშვო ჩაი ქამომილა 200მლ",COL_PRICE:6.80,COL_OLD_PRICE:None,COL_DISCOUNT:None,COL_BRAND:"Hipp",COL_CATEGORY:"ჩაი / წყალი",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"Semper ბავშვის წყალი 1.5ლ",COL_PRICE:4.20,COL_OLD_PRICE:None,   COL_DISCOUNT:None, COL_BRAND:"Semper",COL_CATEGORY:"ჩაი / წყალი",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    {COL_NAME:"Semper ბავშვის წყალი 1.5ლ",COL_PRICE:4.40,COL_OLD_PRICE:None,   COL_DISCOUNT:None, COL_BRAND:"Semper",COL_CATEGORY:"ჩაი / წყალი",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    # ─── დესერტი ─────────────────────────────────────────────
    {COL_NAME:"Semper სპაგეტი ხორცით 190გ",COL_PRICE:6.62,COL_OLD_PRICE:9.45, COL_DISCOUNT:30.0, COL_BRAND:"Semper",COL_CATEGORY:"მზა კვება",COL_SOURCE:"GPC",  COL_URL:"https://gpc.ge"},
    {COL_NAME:"Semper სპაგეტი ხორცით 190გ",COL_PRICE:7.50,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Semper",COL_CATEGORY:"მზა კვება",COL_SOURCE:"PSP",  COL_URL:"https://psp.ge"},
    {COL_NAME:"Gerber კარტოფილი-ქათამი",   COL_PRICE:5.20,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Gerber",COL_CATEGORY:"მზა კვება",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"Gerber კარტოფილი-ქათამი",   COL_PRICE:5.00,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Gerber",COL_CATEGORY:"მზა კვება",COL_SOURCE:"GPC",  COL_URL:"https://gpc.ge"},
    # ─── წვენი ───────────────────────────────────────────────
    {COL_NAME:"HiPP ვაშლის წვენი 200მლ",  COL_PRICE:4.90,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Hipp",   COL_CATEGORY:"წვენი",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
    {COL_NAME:"HiPP ვაშლის წვენი 200მლ",  COL_PRICE:5.10,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Hipp",   COL_CATEGORY:"წვენი",COL_SOURCE:"Aversi",COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"Gerber ატმის წვენი 200მლ",  COL_PRICE:3.80,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Gerber", COL_CATEGORY:"წვენი",COL_SOURCE:"GPC",   COL_URL:"https://gpc.ge"},
    {COL_NAME:"Gerber ატმის წვენი 200მლ",  COL_PRICE:4.00,COL_OLD_PRICE:None,  COL_DISCOUNT:None, COL_BRAND:"Gerber", COL_CATEGORY:"წვენი",COL_SOURCE:"PSP",   COL_URL:"https://psp.ge"},
]
for r in DEMO:
    r.setdefault(COL_NORM_KEY, normalize_key(r[COL_NAME]))
    r.setdefault(COL_UPDATED, datetime.now().strftime("%Y-%m-%d %H:%M"))


# ════════════════════════════════════════════════════════════
# DATA LOADER
# ════════════════════════════════════════════════════════════
@st.cache_data(ttl=600, show_spinner=False)
def load_data(sources: tuple[str, ...], use_demo: bool) -> tuple[pd.DataFrame, bool]:
    if use_demo:
        return pd.DataFrame(DEMO), True

    rows: list[dict] = []
    status = st.status("📡 მარკეტის სკანირება...", expanded=True)

    if "GPC" in sources:
        status.write("⏳ GPC სქრეიფინგი (requests)...")
        try:
            r = scrape_gpc()
            rows.extend(r)
            status.write(f"✅ GPC — {len(r)} SKU")
        except Exception as e:
            status.write(f"⚠️ GPC შეცდომა: {e}")

    if "PSP" in sources:
        status.write("⏳ PSP სქრეიფინგი (Playwright)...")
        try:
            r = scrape_psp()
            rows.extend(r)
            status.write(f"{'✅' if r else '⚠️'} PSP — {len(r)} SKU")
        except Exception as e:
            status.write(f"⚠️ PSP შეცდომა: {e}")

    if "Aversi" in sources:
        status.write("⏳ Aversi სქრეიფინგი (Playwright)...")
        try:
            r = scrape_aversi()
            rows.extend(r)
            status.write(f"{'✅' if r else '⚠️'} Aversi — {len(r)} SKU")
        except Exception as e:
            status.write(f"⚠️ Aversi შეცდომა: {e}")

    status.update(label="✅ სქრეიფინგი დასრულდა!", state="complete", expanded=False)

    if len(rows) < 5:
        return pd.DataFrame(DEMO), True

    df = pd.DataFrame(rows)
    df[COL_UPDATED] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return df, False


# ════════════════════════════════════════════════════════════
# ANALYTICS HELPERS
# ════════════════════════════════════════════════════════════
COLORS = {"PSP": "#1565c0", "Aversi": "#2e7d32", "GPC": "#bf360c"}

def price_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    ქმნის შეწონილ ფასების ინდექსს — საბაზო = GPC.
    ინდექსი > 100  →  GPC-ზე ძვირი
    ინდექსი < 100  →  GPC-ზე იაფი
    """
    avg = df.groupby([COL_CATEGORY, COL_SOURCE])[COL_PRICE].mean().reset_index()
    pivot = avg.pivot(index=COL_CATEGORY, columns=COL_SOURCE, values=COL_PRICE)
    base = pivot.get("GPC", pivot.iloc[:, 0])
    idx = pivot.div(base, axis=0).mul(100).round(1)
    return idx.reset_index()


def sku_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    ერთი და იგივე SKU-ს ფასების შედარების ცხრილი.
    Match: norm_key — პირველი 20 სიმბოლო.
    """
    pivot = (
        df.groupby([COL_NORM_KEY, COL_SOURCE])[COL_PRICE]
        .mean()
        .unstack(COL_SOURCE)
        .reset_index()
    )
    pivot.columns.name = None
    src_cols = [c for c in ["PSP", "Aversi", "GPC"] if c in pivot.columns]

    # სახელი — უგრძეს pivot-ში შევიყვანოთ
    name_map = (
        df.groupby(COL_NORM_KEY)[COL_NAME]
        .agg(lambda x: max(x, key=len))
        .reset_index()
    )
    pivot = pivot.merge(name_map, on=COL_NORM_KEY, how="left")

    if len(src_cols) >= 2:
        pivot["min_price"] = pivot[src_cols].min(axis=1)
        pivot["max_price"] = pivot[src_cols].max(axis=1)
        pivot["სხვაობა (₾)"] = (pivot["max_price"] - pivot["min_price"]).round(2)
        pivot["სხვაობა (%)"] = (
            (pivot["max_price"] - pivot["min_price"]) / pivot["min_price"] * 100
        ).round(1)
        pivot["იაფი წყარო"] = pivot[src_cols].idxmin(axis=1)
        pivot["ძვირი წყარო"] = pivot[src_cols].idxmax(axis=1)

    pivot = pivot.dropna(subset=src_cols, thresh=2)
    return pivot.sort_values("სხვაობა (₾)", ascending=False).reset_index(drop=True)


def brand_share(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby([COL_SOURCE, COL_BRAND])[COL_NAME]
        .count()
        .reset_index(name="SKU_რაოდენობა")
    )


def discount_leaders(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.dropna(subset=[COL_DISCOUNT])
        .sort_values(COL_DISCOUNT, ascending=False)
        .head(20)[[COL_NAME, COL_CATEGORY, COL_BRAND, COL_PRICE, COL_OLD_PRICE, COL_DISCOUNT, COL_SOURCE]]
        .reset_index(drop=True)
    )


def premium_budget_split(df: pd.DataFrame) -> pd.DataFrame:
    """ფასობრივი სეგმენტი (Budget / Mid / Premium) წყაროს მიხედვით."""
    q33 = df[COL_PRICE].quantile(0.33)
    q66 = df[COL_PRICE].quantile(0.66)

    def segment(p):
        if p <= q33:   return "Budget"
        if p <= q66:   return "Mid-Range"
        return "Premium"

    df2 = df.copy()
    df2["სეგმენტი"] = df2[COL_PRICE].apply(segment)
    return (
        df2.groupby([COL_SOURCE, "სეგმენტი"])[COL_NAME]
        .count()
        .reset_index(name="SKU")
    )


def coverage_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """ვინ ყიდის რომელ ბრენდს — და ვის აკლია."""
    all_brands = df[COL_BRAND].unique()
    all_sources = df[COL_SOURCE].unique()
    grid = pd.MultiIndex.from_product(
        [all_sources, all_brands], names=[COL_SOURCE, COL_BRAND]
    ).to_frame(index=False)
    actual = (
        df.groupby([COL_SOURCE, COL_BRAND])[COL_NAME]
        .count()
        .reset_index(name="SKU")
    )
    merged = grid.merge(actual, on=[COL_SOURCE, COL_BRAND], how="left")
    merged["SKU"] = merged["SKU"].fillna(0).astype(int)
    merged["სტატუსი"] = merged["SKU"].apply(
        lambda x: "✅ არის" if x > 0 else "❌ არ არის"
    )
    return merged


def auto_insights(df: pd.DataFrame, matrix: pd.DataFrame) -> list[str]:
    """ავტომატური ტექსტური ინსაიტები."""
    insights = []

    # 1) ყველაზე მეტი ფასდაკლება
    disc = df.dropna(subset=[COL_DISCOUNT])
    if not disc.empty:
        row = disc.loc[disc[COL_DISCOUNT].idxmax()]
        insights.append(
            f"🔥 <b>ყველაზე დიდი ფასდაკლება:</b> <i>{row[COL_NAME]}</i> "
            f"— <b>{row[COL_DISCOUNT]:.0f}%</b> ({row[COL_SOURCE]})"
        )

    # 2) ყველაზე დიდი სხვაობა SKU-ებს შორის
    if "სხვაობა (₾)" in matrix.columns and not matrix.empty:
        top = matrix.iloc[0]
        insights.append(
            f"💰 <b>ყველაზე დიდი ფასის სხვაობა:</b> <i>{top[COL_NAME]}</i> "
            f"— ₾<b>{top['სხვაობა (₾)']:.2f}</b> ({top.get('იაფი წყარო','?')} vs {top.get('ძვირი წყარო','?')})"
        )

    # 3) რომელი წყარო ყველაზე იაფია საშუალოდ
    avg_src = df.groupby(COL_SOURCE)[COL_PRICE].mean()
    cheapest = avg_src.idxmin()
    insights.append(
        f"🏆 <b>ყველაზე დაბალი საშუალო ფასი:</b> <b>{cheapest}</b> "
        f"(₾{avg_src[cheapest]:.2f})"
    )

    # 4) პრემიუმ კატეგორია
    avg_cat = df.groupby(COL_CATEGORY)[COL_PRICE].mean()
    prem = avg_cat.idxmax()
    insights.append(
        f"👑 <b>ყველაზე ძვირი კატეგორია:</b> <b>{prem}</b> "
        f"(საშ. ₾{avg_cat[prem]:.2f})"
    )

    # 5) SKU გადახურვა
    pivot_src = df.groupby([COL_NORM_KEY, COL_SOURCE]).size().unstack(COL_SOURCE).notna()
    n_all3 = int(pivot_src.all(axis=1).sum()) if pivot_src.shape[1] == 3 else 0
    insights.append(
        f"🔗 <b>ყველა 3 წყაროში ნაყიდი SKU:</b> <b>{n_all3}</b> პოზიცია"
    )

    return insights


# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("⚙️ კონტროლ პანელი")

    # Playwright check
    try:
        from playwright.sync_api import sync_playwright as _pw  # noqa
        pw_ok = True
    except ImportError:
        pw_ok = False

    if pw_ok:
        st.success("✅ Playwright — OK")
    else:
        st.warning("⚠️ Playwright არ არის\n\n`pip install playwright`\n`playwright install chromium`")

    use_demo = st.toggle(
        "🎭 Demo მონაცემები",
        value=(not pw_ok),
        help="გამორთე რეალური სქრეიფინგისთვის"
    )
    st.divider()

    sel_sources = st.multiselect(
        "🏪 წყაროები",
        ["PSP", "Aversi", "GPC"],
        default=["PSP", "Aversi", "GPC"],
    )
    st.divider()

    st.markdown("**წყაროები:**")
    st.markdown(
        '<span class="badge b-psp">PSP</span>'
        '<span class="badge b-aversi">Aversi</span>'
        '<span class="badge b-gpc">GPC</span>',
        unsafe_allow_html=True
    )
    st.divider()
    if st.button("🔄 ხელახლა სკანირება", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()


# ════════════════════════════════════════════════════════════
# DATA LOAD
# ════════════════════════════════════════════════════════════
st.title("🍼 ბავშვის კვება · ფასების ინდექსი")
st.markdown(
    "**კატეგორიის მენეჯმენტის Pro-Dashboard** &nbsp;|&nbsp; "
    "PSP &nbsp;·&nbsp; Aversi &nbsp;·&nbsp; GPC"
)

df_raw, is_demo = load_data(tuple(sel_sources), use_demo)

if is_demo:
    st.info("🎭 **Demo მონაცემები** — Sidebar-ში გამორთე toggle რეალური სქრეიფინგისთვის.", icon="ℹ️")

df = df_raw.copy()

if df.empty:
    st.error("მონაცემები ვერ ჩაიტვირთა.")
    st.stop()

updated_at = df[COL_UPDATED].iloc[0] if COL_UPDATED in df.columns else "—"
st.caption(
    f"🕐 განახლება: **{updated_at}** &nbsp;|&nbsp; "
    f"📦 სულ SKU: **{len(df)}** &nbsp;|&nbsp; "
    f"🏪 წყარო: **{df[COL_SOURCE].nunique()}** &nbsp;|&nbsp; "
    f"🏷 ბრენდი: **{df[COL_BRAND].nunique()}**"
)
st.divider()

# ════════════════════════════════════════════════════════════
# GLOBAL FILTERS BAR
# ════════════════════════════════════════════════════════════
fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 3])
with fc1:
    cats = ["ყველა"] + sorted(df[COL_CATEGORY].unique().tolist())
    sel_cat = st.selectbox("📂 კატეგორია", cats)
with fc2:
    brands = ["ყველა"] + sorted(df[COL_BRAND].unique().tolist())
    sel_brand = st.selectbox("🏷 ბრენდი", brands)
with fc3:
    pmin = float(df[COL_PRICE].min())
    pmax = float(df[COL_PRICE].max())
    price_range = st.slider("💰 ფასი (₾)", pmin, pmax, (pmin, pmax), step=0.5)
with fc4:
    keyword = st.text_input("🔍 ძიება", placeholder="მაგ: HiPP, Cerelac, 800...")

# ფილტრაცია
fdf = df.copy()
if sel_cat   != "ყველა":  fdf = fdf[fdf[COL_CATEGORY] == sel_cat]
if sel_brand != "ყველა":  fdf = fdf[fdf[COL_BRAND] == sel_brand]
fdf = fdf[fdf[COL_PRICE].between(price_range[0], price_range[1])]
if keyword.strip():
    fdf = fdf[fdf[COL_NAME].str.contains(keyword.strip(), case=False, na=False)]

if fdf.empty:
    st.warning("ფილტრის პირობებს შესაბამისი პროდუქტი ვერ მოიძებნა.")
    st.stop()

st.caption(f"ფილტრი: **{len(fdf)}** SKU")
st.divider()

# ════════════════════════════════════════════════════════════
# KPI ROW
# ════════════════════════════════════════════════════════════
k1, k2, k3, k4, k5, k6 = st.columns(6)
avg_by_src = fdf.groupby(COL_SOURCE)[COL_PRICE].mean()
cheapest_src = avg_by_src.idxmin() if not avg_by_src.empty else "—"
priciest_src = avg_by_src.idxmax() if not avg_by_src.empty else "—"
disc_df = fdf.dropna(subset=[COL_DISCOUNT])

with k1: st.metric("📦 SKU სულ",      len(fdf))
with k2: st.metric("🏷 ბრენდი",       fdf[COL_BRAND].nunique())
with k3: st.metric("💰 საშ. ფასი",    f"₾{fdf[COL_PRICE].mean():.2f}")
with k4: st.metric("📉 საშ. დისქ.",   f"{disc_df[COL_DISCOUNT].mean():.1f}%" if not disc_df.empty else "—")
with k5: st.metric("🏆 იაფი წყარო",   cheapest_src)
with k6: st.metric("💎 ძვირი წყარო",  priciest_src)

st.divider()


# ════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════
(tab_overview, tab_sku, tab_index,
 tab_brand, tab_discount, tab_segment,
 tab_coverage, tab_full) = st.tabs([
    "📊 მიმოხილვა",
    "⚔️ SKU-ს ომი",
    "📈 ფასების ინდექსი",
    "🏷 ბრენდული ანალიზი",
    "🔥 ფასდაკლებები",
    "💎 სეგმენტები",
    "🗺 გადახურვა",
    "📋 სრული სია",
])


# ─────────────────────────────────────────────────────────────
# TAB 1 · მიმოხილვა
# ─────────────────────────────────────────────────────────────
with tab_overview:
    # ── Auto-Insights ────────────────────────────────────────
    mat = sku_matrix(fdf)
    insights = auto_insights(fdf, mat)

    st.subheader("🤖 ავტო-ინსაიტები")
    cols_i = st.columns(len(insights))
    for col, text in zip(cols_i, insights):
        with col:
            st.markdown(f'<div class="insight-box">{text}</div>', unsafe_allow_html=True)

    st.divider()

    # ── Bar: საშ. ფასი კატ × წყარო ──────────────────────────
    st.subheader("📊 საშუალო ფასი — კატეგორია × წყარო")
    avg_cat = (
        fdf.groupby([COL_CATEGORY, COL_SOURCE])[COL_PRICE]
        .mean().reset_index()
        .rename(columns={COL_PRICE: "საშ. ფასი (₾)"})
    )
    fig_bar = px.bar(
        avg_cat, x=COL_CATEGORY, y="საშ. ფასი (₾)", color=COL_SOURCE,
        barmode="group", color_discrete_map=COLORS,
        text_auto=".2f",
        labels={COL_CATEGORY: "", COL_SOURCE: "წყარო"},
    )
    fig_bar.update_traces(textfont_size=10, textposition="outside")
    fig_bar.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        height=420, uniformtext_minsize=8,
        legend_title="წყარო",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Treemap: SKU count by brand × source ─────────────────
    st.subheader("🗂 SKU სტრუქტურა — ბრენდი × წყარო")
    tree_df = (
        fdf.groupby([COL_SOURCE, COL_BRAND, COL_CATEGORY])[COL_NAME]
        .count().reset_index(name="SKU")
    )
    fig_tree = px.treemap(
        tree_df,
        path=[COL_SOURCE, COL_CATEGORY, COL_BRAND],
        values="SKU",
        color=COL_SOURCE,
        color_discrete_map=COLORS,
    )
    fig_tree.update_layout(height=400, margin=dict(t=20, l=0, r=0, b=0))
    st.plotly_chart(fig_tree, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# TAB 2 · SKU-ს ომი (Price War Matrix)
# ─────────────────────────────────────────────────────────────
with tab_sku:
    st.subheader("⚔️ SKU Price War — იდენტური პროდუქტების ფასების შედარება")
    st.caption(
        "მხოლოდ ის SKU-ები, რომლებიც მინიმუმ 2 წყაროში გვხვდება. "
        "შეფერადება: 🟢 ყველაზე იაფი | 🔴 ყველაზე ძვირი"
    )

    mat = sku_matrix(fdf)
    src_cols = [c for c in ["PSP", "Aversi", "GPC"] if c in mat.columns]

    if mat.empty or len(src_cols) < 2:
        st.info("შედარებისთვის საჭიროა მინიმუმ 2 წყარო.")
    else:
        # ── Heatmap: ფასების სხვაობა % ────────────────────────
        hm_data = mat.dropna(subset=["სხვაობა (%)"], how="any").head(20)
        if not hm_data.empty:
            fig_hm = go.Figure(data=go.Bar(
                x=hm_data[COL_NAME].str[:40],
                y=hm_data["სხვაობა (%)"],
                marker_color=hm_data["სხვაობა (%)"],
                marker_colorscale="RdYlGn_r",
                text=hm_data["სხვაობა (%)"].apply(lambda v: f"{v:.1f}%"),
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "სხვაობა: %{y:.1f}%<extra></extra>"
                ),
            ))
            fig_hm.update_layout(
                title="Top 20 — ყველაზე მაღალი ფასების სხვაობა (%)",
                xaxis_tickangle=-35,
                plot_bgcolor="white", paper_bgcolor="white",
                height=420,
                yaxis_title="სხვაობა (%)",
                xaxis_title="",
            )
            st.plotly_chart(fig_hm, use_container_width=True)

        # ── ცხრილი ────────────────────────────────────────────
        display_mat = mat[[COL_NAME] + src_cols + ["სხვაობა (₾)", "სხვაობა (%)", "იაფი წყარო", "ძვირი წყარო"]].copy()

        fmt = {c: "₾{:.2f}" for c in src_cols}
        fmt["სხვაობა (₾)"] = "₾{:.2f}"
        fmt["სხვაობა (%)"] = "{:.1f}%"

        def highlight_row(row):
            styles = [""] * len(row)
            if "სხვაობა (%)" in row.index:
                diff = row["სხვაობა (%)"]
                if isinstance(diff, float):
                    if diff > 15:
                        return ["background-color:#fff3cd"] * len(row)
            return styles

        styled = (
            display_mat.style
            .format(fmt, na_rep="—")
            .apply(highlight_row, axis=1)
            .background_gradient(subset=["სხვაობა (₾)"], cmap="YlOrRd")
        )
        st.dataframe(styled, use_container_width=True, height=460, hide_index=True)

        # ── Winner Score ───────────────────────────────────────
        st.subheader("🏅 წყაროს მოგება SKU-ების მიხედვით")
        wins = mat["იაფი წყარო"].value_counts().reset_index()
        wins.columns = ["წყარო", "SKU სადაც იაფია"]
        fig_wins = px.bar(
            wins, x="წყარო", y="SKU სადაც იაფია",
            color="წყარო", color_discrete_map=COLORS,
            text="SKU სადაც იაფია",
        )
        fig_wins.update_traces(textposition="outside")
        fig_wins.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            height=320, showlegend=False,
        )
        st.plotly_chart(fig_wins, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# TAB 3 · ფასების ინდექსი (rebased to GPC=100)
# ─────────────────────────────────────────────────────────────
with tab_index:
    st.subheader("📈 ფასების ინდექსი (საბაზო = GPC · 100)")
    st.caption(
        "ინდექსი > 100 → GPC-ზე ძვირი &nbsp;|&nbsp; "
        "ინდექსი < 100 → GPC-ზე იაფი"
    )
    idx_df = price_index(fdf)
    src_idx_cols = [c for c in ["PSP", "Aversi", "GPC"] if c in idx_df.columns]

    if len(src_idx_cols) < 2:
        st.info("ინდექსისთვის საჭიროა მინიმუმ 2 წყარო.")
    else:
        fig_idx = px.bar(
            idx_df.melt(id_vars=COL_CATEGORY, value_vars=src_idx_cols,
                        var_name="წყარო", value_name="ინდექსი"),
            x=COL_CATEGORY, y="ინდექსი", color="წყარო",
            barmode="group", color_discrete_map=COLORS,
            text_auto=".1f",
            labels={COL_CATEGORY: ""},
        )
        fig_idx.add_hline(y=100, line_dash="dash", line_color="gray",
                          annotation_text="საბაზო (GPC=100)")
        fig_idx.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            height=420, legend_title="წყარო",
        )
        st.plotly_chart(fig_idx, use_container_width=True)

        # ── Radar: საბოლოო ინდექსი ────────────────────────────
        overall = fdf.groupby(COL_SOURCE)[COL_PRICE].mean()
        if "GPC" in overall:
            base_val = overall["GPC"]
            radar_src = [s for s in ["PSP", "Aversi", "GPC"] if s in overall]
            fig_radar = go.Figure()
            for src in radar_src:
                cats_r = idx_df[COL_CATEGORY].tolist()
                vals = idx_df.get(src, pd.Series([100]*len(cats_r))).tolist()
                vals += vals[:1]
                cats_r_loop = cats_r + cats_r[:1]
                fig_radar.add_trace(go.Scatterpolar(
                    r=vals, theta=cats_r_loop,
                    fill="toself", name=src,
                    line_color=COLORS.get(src, "#888"),
                ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[70, 130])),
                showlegend=True, height=420,
                title="ფასების ინდექსი — Radar View",
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        st.dataframe(
            idx_df.style.format({c: "{:.1f}" for c in src_idx_cols}, na_rep="—")
                        .background_gradient(cmap="RdYlGn_r", subset=src_idx_cols),
            use_container_width=True,
            hide_index=True,
        )


# ─────────────────────────────────────────────────────────────
# TAB 4 · ბრენდული ანალიზი
# ─────────────────────────────────────────────────────────────
with tab_brand:
    st.subheader("🏷 ბრენდული ანალიზი — SKU Count & ფასი")

    c_left, c_right = st.columns(2)

    with c_left:
        bs = brand_share(fdf)
        fig_bs = px.bar(
            bs, x=COL_BRAND, y="SKU_რაოდენობა", color=COL_SOURCE,
            barmode="stack", color_discrete_map=COLORS,
            title="SKU რაოდენობა ბრენდ × წყარო",
            labels={COL_BRAND: "", "SKU_რაოდენობა": "SKU"},
        )
        fig_bs.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            height=380, xaxis_tickangle=-30,
        )
        st.plotly_chart(fig_bs, use_container_width=True)

    with c_right:
        # საშ. ფასი ბრენდების მიხედვით
        brand_price = (
            fdf.groupby([COL_BRAND, COL_SOURCE])[COL_PRICE]
            .mean().reset_index()
            .rename(columns={COL_PRICE: "საშ. ფასი (₾)"})
        )
        fig_bp = px.scatter(
            brand_price, x=COL_BRAND, y="საშ. ფასი (₾)",
            color=COL_SOURCE, size="საშ. ფასი (₾)",
            color_discrete_map=COLORS,
            title="საშ. ფასი ბრენდის მიხედვით",
            labels={COL_BRAND: ""},
        )
        fig_bp.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            height=380, xaxis_tickangle=-30,
        )
        st.plotly_chart(fig_bp, use_container_width=True)

    # ── ბრენდის ფასების სპექტრი ──────────────────────────────
    st.subheader("📦 ბრენდების ფასების სპექტრი")
    fig_box = px.box(
        fdf, x=COL_BRAND, y=COL_PRICE, color=COL_SOURCE,
        color_discrete_map=COLORS, points="outliers",
        labels={COL_BRAND: "", COL_PRICE: "ფასი (₾)"},
    )
    fig_box.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        height=420, xaxis_tickangle=-30,
    )
    st.plotly_chart(fig_box, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# TAB 5 · ფასდაკლებები
# ─────────────────────────────────────────────────────────────
with tab_discount:
    st.subheader("🔥 ფასდაკლებების ანალიზი")
    disc = discount_leaders(fdf)

    if disc.empty:
        st.info("მონაცემებში ფასდაკლება ვერ მოიძებნა.")
    else:
        d1, d2 = st.columns(2)
        with d1:
            fig_disc = px.bar(
                disc.head(15),
                x=COL_DISCOUNT, y=COL_NAME,
                orientation="h",
                color=COL_SOURCE, color_discrete_map=COLORS,
                text=disc.head(15)[COL_DISCOUNT].apply(lambda v: f"{v:.0f}%"),
                title="Top 15 — ყველაზე მაღალი ფასდაკლება",
                labels={COL_DISCOUNT: "ფასდაკლება (%)", COL_NAME: ""},
            )
            fig_disc.update_traces(textposition="outside")
            fig_disc.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                height=480, showlegend=True,
            )
            st.plotly_chart(fig_disc, use_container_width=True)

        with d2:
            # Scatter: ძველი vs ახალი ფასი
            disc_scatter = fdf.dropna(subset=[COL_OLD_PRICE, COL_DISCOUNT]).copy()
            if not disc_scatter.empty:
                fig_sc = px.scatter(
                    disc_scatter,
                    x=COL_OLD_PRICE, y=COL_PRICE,
                    color=COL_SOURCE, color_discrete_map=COLORS,
                    size=COL_DISCOUNT,
                    hover_data=[COL_NAME, COL_DISCOUNT],
                    title="ძველი vs ახალი ფასი (ზომა = ფასდაკლება%)",
                    labels={COL_OLD_PRICE: "ძველი ფასი (₾)", COL_PRICE: "ახალი ფასი (₾)"},
                )
                # diagonal reference line
                max_p = float(disc_scatter[[COL_OLD_PRICE, COL_PRICE]].max().max())
                fig_sc.add_trace(go.Scatter(
                    x=[0, max_p], y=[0, max_p],
                    mode="lines",
                    line=dict(dash="dot", color="gray"),
                    name="ფასი=ფასი",
                ))
                fig_sc.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    height=480,
                )
                st.plotly_chart(fig_sc, use_container_width=True)
            else:
                st.info("ძველი ფასების მონაცემი არ არის.")

        # ── ფასდაკლებების ცხრილი ──────────────────────────────
        st.dataframe(
            disc.style.format({
                COL_PRICE:     "₾{:.2f}",
                COL_OLD_PRICE: "₾{:.2f}",
                COL_DISCOUNT:  "{:.1f}%",
            }, na_rep="—").background_gradient(subset=[COL_DISCOUNT], cmap="YlOrRd"),
            use_container_width=True,
            height=380,
            hide_index=True,
        )


# ─────────────────────────────────────────────────────────────
# TAB 6 · სეგმენტები (Budget / Mid / Premium)
# ─────────────────────────────────────────────────────────────
with tab_segment:
    st.subheader("💎 ფასობრივი სეგმენტაცია — Budget · Mid-Range · Premium")
    seg = premium_budget_split(fdf)

    s1, s2 = st.columns(2)
    with s1:
        fig_seg = px.bar(
            seg, x="სეგმენტი", y="SKU", color=COL_SOURCE,
            barmode="group", color_discrete_map=COLORS,
            title="SKU განაწილება სეგმენტ × წყარო",
            category_orders={"სეგმენტი": ["Budget", "Mid-Range", "Premium"]},
            text="SKU",
        )
        fig_seg.update_traces(textposition="outside")
        fig_seg.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", height=380,
        )
        st.plotly_chart(fig_seg, use_container_width=True)

    with s2:
        fig_sun = px.sunburst(
            fdf.assign(სეგმენტი=pd.cut(
                fdf[COL_PRICE],
                bins=[0, fdf[COL_PRICE].quantile(0.33),
                      fdf[COL_PRICE].quantile(0.66),
                      fdf[COL_PRICE].max()+1],
                labels=["Budget", "Mid-Range", "Premium"]
            )),
            path=[COL_SOURCE, "სეგმენტი", COL_BRAND],
            values=COL_PRICE,
            color=COL_SOURCE,
            color_discrete_map=COLORS,
            title="SKU სტრუქტურა — Sunburst",
        )
        fig_sun.update_layout(height=380, margin=dict(t=40, l=0, r=0, b=0))
        st.plotly_chart(fig_sun, use_container_width=True)

    # ── Box per segment ───────────────────────────────────────
    fdf2 = fdf.copy()
    fdf2["სეგმენტი"] = pd.cut(
        fdf2[COL_PRICE],
        bins=[0, fdf2[COL_PRICE].quantile(0.33),
              fdf2[COL_PRICE].quantile(0.66),
              fdf2[COL_PRICE].max()+1],
        labels=["Budget", "Mid-Range", "Premium"]
    ).astype(str)
    fig_seg_box = px.violin(
        fdf2, x="სეგმენტი", y=COL_PRICE, color=COL_SOURCE,
        color_discrete_map=COLORS, box=True, points="outliers",
        category_orders={"სეგმენტი": ["Budget", "Mid-Range", "Premium"]},
        labels={COL_PRICE: "ფასი (₾)", "სეგმენტი": ""},
        title="ფასების განაწილება სეგმენტების მიხედვით",
    )
    fig_seg_box.update_layout(
        plot_bgcolor="white", paper_bgcolor="white", height=380,
    )
    st.plotly_chart(fig_seg_box, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# TAB 7 · გადახურვის რუკა (Coverage Heatmap)
# ─────────────────────────────────────────────────────────────
with tab_coverage:
    st.subheader("🗺 SKU გადახურვა — ვინ ყიდის რომელ ბრენდს")
    cov = coverage_gaps(fdf)

    # Pivot for heatmap
    cov_pivot = cov.pivot(index=COL_BRAND, columns=COL_SOURCE, values="SKU").fillna(0)
    fig_cov = px.imshow(
        cov_pivot,
        color_continuous_scale=[[0, "#fff0f0"], [0.01, "#ffe0e0"], [1, "#1565c0"]],
        text_auto=True,
        aspect="auto",
        title="SKU რაოდენობა ბრენდ × წყარო (0 = არ ყიდის)",
        labels={"color": "SKU Count"},
    )
    fig_cov.update_layout(height=420, margin=dict(t=60))
    st.plotly_chart(fig_cov, use_container_width=True)

    # ── White-Spot ანალიზი ────────────────────────────────────
    st.subheader("❌ White-Spot — რომელი ბრენდი რომელ წყაროში არ არის")
    gaps = cov[cov["SKU"] == 0][[COL_SOURCE, COL_BRAND]].copy()
    if gaps.empty:
        st.success("🎉 ყველა ბრენდი ყველა წყაროშია!")
    else:
        gap_pivot = gaps.groupby(COL_SOURCE)[COL_BRAND].apply(list).reset_index()
        gap_pivot.columns = ["წყარო", "დაკარგული ბრენდები"]
        gap_pivot["დაკარგული ბრენდები"] = gap_pivot["დაკარგული ბრენდები"].apply(
            lambda lst: ", ".join(sorted(set(lst)))
        )
        st.dataframe(gap_pivot, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────
# TAB 8 · სრული სია
# ─────────────────────────────────────────────────────────────
with tab_full:
    st.subheader("📋 სრული პროდუქტების სია")

    show = fdf[[COL_NAME, COL_CATEGORY, COL_BRAND, COL_SOURCE,
                COL_PRICE, COL_OLD_PRICE, COL_DISCOUNT, COL_URL]].copy()

    styled_full = show.style.format({
        COL_PRICE:     "₾{:.2f}",
        COL_OLD_PRICE: "₾{:.2f}",
        COL_DISCOUNT:  "{:.1f}%",
    }, na_rep="—").background_gradient(subset=[COL_PRICE], cmap="YlGn")

    st.dataframe(
        styled_full,
        use_container_width=True,
        height=520,
        hide_index=True,
        column_config={
            COL_URL: st.column_config.LinkColumn("🔗 ლინკი", display_text="გახსნა"),
        },
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    csv = show.drop(columns=[COL_URL]).to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "⬇️ CSV ჩამოტვირთვა",
        data=csv,
        file_name=f"baby_food_price_index_{ts}.csv",
        mime="text/csv",
        use_container_width=True,
    )
