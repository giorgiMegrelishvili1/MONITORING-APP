# ============================================================
# app.py — 🍼 ბავშვის კვება: Pro-Level ფასების ინდექსი
# PSP · Aversi · GPC
# ============================================================
from __future__ import annotations

import os
import sys
import re
import subprocess
from datetime import datetime

# 🚀 Playwright-ის ავტომატური ინსტალაცია Streamlit Cloud-ისთვის
try:
    if not os.path.exists("/home/appuser/.cache/ms-playwright"):
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True, timeout=300)
        subprocess.run([sys.executable, "-m", "playwright", "install-deps"], check=True, timeout=300)
except Exception:
    pass

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ── კონფიგი და იმპორტები ──────────────────────────────────
try:
    from config import (
        COL_NAME, COL_PRICE, COL_OLD_PRICE, COL_DISCOUNT,
        COL_BRAND, COL_CATEGORY, COL_SOURCE, COL_URL,
        COL_UPDATED, COL_NORM_KEY,
    )
    from gpc import scrape_gpc
    from psp import scrape_psp
    from aversi import scrape_aversi
    from common import normalize_key
except Exception:
    COL_NAME, COL_PRICE, COL_OLD_PRICE = "სახელი", "ფასი", "ძველი_ფასი"
    COL_DISCOUNT, COL_BRAND, COL_CATEGORY = "ფასდაკლება", "ბრენდი", "კატეგორია"
    COL_SOURCE, COL_URL, COL_UPDATED = "წყარო", "url", "განახლდა"
    COL_NORM_KEY = "norm_key"
    
    def normalize_key(text: str) -> str:
        return re.sub(r'[^a-zA-Z0-9ა-ჰ]', '', str(text)).lower()[:25]

# ════════════════════════════════════════════════════════════
# PAGE SETUP & FIXED CLEAN CSS
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="🍼 ბავშვის კვება · PRO ფასების ინდექსი",
    page_icon="🍼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# სწორად დახურული html/style თეგები რომ ტექსტად არ გამოჩნდეს
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc;
    }
    
    .pro-hero {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
        border-radius: 20px;
        padding: 30px 35px;
        margin-bottom: 25px;
        color: #ffffff;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }
    
    .pro-eyebrow {
        background: rgba(255, 255, 255, 0.15);
        color: #67e8f9;
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 5px 12px;
        border-radius: 99px;
        display: inline-block;
        margin-bottom: 10px;
    }
    
    .pro-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.2;
    }
    
    .pro-subtitle {
        color: #cbd5e1;
        font-size: 0.95rem;
        margin-top: 8px;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 15px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .insight-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #4f46e5;
        border-radius: 12px;
        padding: 15px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# DEMO DATA & DATA CLEANING ENGINE
# ════════════════════════════════════════════════════════════
DEMO = [
    {COL_NAME:"HiPP Organic 1 (800გ)", COL_PRICE:89.90, COL_OLD_PRICE:None, COL_DISCOUNT:None, COL_BRAND:"Hipp", COL_CATEGORY:"რძის ნაზავი", COL_SOURCE:"PSP", COL_URL:"https://psp.ge"},
    {COL_NAME:"HiPP Organic 1 (800გ)", COL_PRICE:92.50, COL_OLD_PRICE:None, COL_DISCOUNT:None, COL_BRAND:"Hipp", COL_CATEGORY:"რძის ნაზავი", COL_SOURCE:"Aversi", COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"HiPP Organic 1 (800გ)", COL_PRICE:88.00, COL_OLD_PRICE:None, COL_DISCOUNT:None, COL_BRAND:"Hipp", COL_CATEGORY:"რძის ნაზავი", COL_SOURCE:"GPC", COL_URL:"https://gpc.ge"},
    {COL_NAME:"NAN Optipro 1 (800გ)", COL_PRICE:72.00, COL_OLD_PRICE:80.00, COL_DISCOUNT:10.0, COL_BRAND:"Nan", COL_CATEGORY:"რძის ნაზავი", COL_SOURCE:"PSP", COL_URL:"https://psp.ge"},
    {COL_NAME:"NAN Optipro 1 (800გ)", COL_PRICE:74.50, COL_OLD_PRICE:None, COL_DISCOUNT:None, COL_BRAND:"Nan", COL_CATEGORY:"რძის ნაზავი", COL_SOURCE:"Aversi", COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"NAN Optipro 1 (800გ)", COL_PRICE:71.00, COL_OLD_PRICE:None, COL_DISCOUNT:None, COL_BRAND:"Nan", COL_CATEGORY:"რძის ნაზავი", COL_SOURCE:"GPC", COL_URL:"https://gpc.ge"},
    {COL_NAME:"Nutrilon Premium 1 (400გ)", COL_PRICE:45.00, COL_OLD_PRICE:50.00, COL_DISCOUNT:10.0, COL_BRAND:"Nutrilon", COL_CATEGORY:"რძის ნაზავი", COL_SOURCE:"PSP", COL_URL:"https://psp.ge"},
    {COL_NAME:"Nutrilon Premium 1 (400გ)", COL_PRICE:46.50, COL_OLD_PRICE:None, COL_DISCOUNT:None, COL_BRAND:"Nutrilon", COL_CATEGORY:"რძის ნაზავი", COL_SOURCE:"Aversi", COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"Nutrilon Premium 1 (400გ)", COL_PRICE:44.00, COL_OLD_PRICE:None, COL_DISCOUNT:None, COL_BRAND:"Nutrilon", COL_CATEGORY:"რძის ნაზავი", COL_SOURCE:"GPC", COL_URL:"https://gpc.ge"},
    {COL_NAME:"Heinz ბრინჯის ფაფა (200გ)", COL_PRICE:9.90, COL_OLD_PRICE:None, COL_DISCOUNT:None, COL_BRAND:"Heinz", COL_CATEGORY:"ფაფა", COL_SOURCE:"PSP", COL_URL:"https://psp.ge"},
    {COL_NAME:"Heinz ბრინჯის ფაფა (200გ)", COL_PRICE:10.20, COL_OLD_PRICE:None, COL_DISCOUNT:None, COL_BRAND:"Heinz", COL_CATEGORY:"ფაფა", COL_SOURCE:"Aversi", COL_URL:"https://shop.aversi.ge"},
    {COL_NAME:"Heinz ბრინჯის ფაფა (200გ)", COL_PRICE:9.50, COL_OLD_PRICE:None, COL_DISCOUNT:None, COL_BRAND:"Heinz", COL_CATEGORY:"ფაფა", COL_SOURCE:"GPC", COL_URL:"https://gpc.ge"},
    {COL_NAME:"Semper ვაშლი 80გ", COL_PRICE:3.43, COL_OLD_PRICE:4.90, COL_DISCOUNT:30.0, COL_BRAND:"Semper", COL_CATEGORY:"პიურე", COL_SOURCE:"GPC", COL_URL:"https://gpc.ge"},
    {COL_NAME:"Semper ვაშლი 80გ", COL_PRICE:3.70, COL_OLD_PRICE:None, COL_DISCOUNT:None, COL_BRAND:"Semper", COL_CATEGORY:"პიურე", COL_SOURCE:"PSP", COL_URL:"https://psp.ge"},
    {COL_NAME:"Semper ვაშლი 80გ", COL_PRICE:3.55, COL_OLD_PRICE:None, COL_DISCOUNT:None, COL_BRAND:"Semper", COL_CATEGORY:"პიურე", COL_SOURCE:"Aversi", COL_URL:"https://shop.aversi.ge"},
]

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df[COL_PRICE] = pd.to_numeric(df[COL_PRICE], errors='coerce')
    df = df[df[COL_PRICE] > 0]
    df[COL_NAME] = df[COL_NAME].astype(str).str.strip()
    df[COL_BRAND] = df[COL_BRAND].astype(str).str.strip().str.capitalize()
    df[COL_CATEGORY] = df[COL_CATEGORY].astype(str).str.strip()
    df[COL_NORM_KEY] = df[COL_NAME].apply(normalize_key)
    return df.drop_duplicates(subset=[COL_SOURCE, COL_NORM_KEY], keep='last')

@st.cache_data(ttl=600, show_spinner=False)
def load_data(sources: tuple[str, ...], use_demo: bool):
    if use_demo:
        df_demo = pd.DataFrame(DEMO)
        df_demo[COL_UPDATED] = datetime.now().strftime("%Y-%m-%d %H:%M")
        return clean_dataframe(df_demo), True

    rows = []
    if "GPC" in sources and 'scrape_gpc' in globals():
        try: rows.extend(scrape_gpc())
        except Exception: pass
    if "PSP" in sources and 'scrape_psp' in globals():
        try: rows.extend(scrape_psp())
        except Exception: pass
    if "Aversi" in sources and 'scrape_aversi' in globals():
        try: rows.extend(scrape_aversi())
        except Exception: pass

    if len(rows) < 3:
        df_demo = pd.DataFrame(DEMO)
        df_demo[COL_UPDATED] = datetime.now().strftime("%Y-%m-%d %H:%M")
        return clean_dataframe(df_demo), True

    df = pd.DataFrame(rows)
    df[COL_UPDATED] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return clean_dataframe(df), False

def get_sku_matrix(df: pd.DataFrame) -> pd.DataFrame:
    pivot = df.groupby([COL_NORM_KEY, COL_SOURCE])[COL_PRICE].min().unstack(COL_SOURCE).reset_index()
    src_cols = [c for c in ["PSP", "Aversi", "GPC"] if c in pivot.columns]
    
    name_map = df.groupby(COL_NORM_KEY)[COL_NAME].agg(lambda x: max(x, key=len)).reset_index()
    pivot = pivot.merge(name_map, on=COL_NORM_KEY, how="left")

    if len(src_cols) >= 2:
        pivot["min_price"] = pivot[src_cols].min(axis=1)
        pivot["max_price"] = pivot[src_cols].max(axis=1)
        pivot["სხვაობა (₾)"] = (pivot["max_price"] - pivot["min_price"]).round(2)
        pivot["სხვაობა (%)"] = ((pivot["max_price"] - pivot["min_price"]) / pivot["min_price"] * 100).round(1)
        pivot["იაფი წყარო"] = pivot[src_cols].idxmin(axis=1)

    return pivot.dropna(subset=src_cols, thresh=2).sort_values("სხვაობა (₾)", ascending=False)

# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("⚙️ პარამეტრები")
    use_demo = st.toggle("🎭 Demo მონაცემები", value=True)
    sel_sources = st.multiselect("🏪 აფთიაქები", ["PSP", "Aversi", "GPC"], default=["PSP", "Aversi", "GPC"])
    
    if st.button("🔄 განახლება", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

# ════════════════════════════════════════════════════════════
# HERO & METRICS
# ════════════════════════════════════════════════════════════
st.markdown("""
<div class="pro-hero">
  <span class="pro-eyebrow">Category Management Pro</span>
  <div class="pro-title">ბავშვის კვება — ფასების ინდექსი</div>
  <div class="pro-subtitle">PSP · Aversi · GPC — ავტომატური მონიტორინგი და შედარებითი ანალიზი</div>
</div>
""", unsafe_allow_html=True)

df_raw, is_demo = load_data(tuple(sel_sources), use_demo)
df = df_raw.copy()

if is_demo:
    st.info("💡 **Demo რეჟიმი აქტიურია.** რეალური სქრეიფინგისთვის გამორთეთ Toggle გვერდითა პანელში.", icon="ℹ️")

# ── FILTERS ────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns([2, 2, 2, 3])
with c1:
    cats = ["ყველა"] + sorted(df[COL_CATEGORY].unique().tolist())
    sel_cat = st.selectbox("📂 კატეგორია", cats)
with c2:
    brands = ["ყველა"] + sorted(df[COL_BRAND].unique().tolist())
    sel_brand = st.selectbox("🏷 ბრენდი", brands)
with c3:
    pmin = float(df[COL_PRICE].min()) if not df.empty else 0.0
    pmax = float(df[COL_PRICE].max()) if not df.empty else 100.0
    prange = st.slider("💰 ფასი (₾)", pmin, pmax, (pmin, pmax))
with c4:
    keyword = st.text_input("🔍 ძიება", placeholder="მაგ: HiPP, Organic...")

# Filter Logic
if sel_cat != "ყველა": df = df[df[COL_CATEGORY] == sel_cat]
if sel_brand != "ყველა": df = df[df[COL_BRAND] == sel_brand]
df = df[df[COL_PRICE].between(prange[0], prange[1])]
if keyword.strip():
    df = df[df[COL_NAME].str.contains(keyword.strip(), case=False, na=False)]

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
avg_src = df.groupby(COL_SOURCE)[COL_PRICE].mean()
cheapest = avg_src.idxmin() if not avg_src.empty else "—"

m1.metric("📦 სულ SKU", len(df))
m2.metric("🏷 ბრენდები", df[COL_BRAND].nunique())
m3.metric("💰 საშუალო ფასი", f"₾{df[COL_PRICE].mean():.2f}" if not df.empty else "—")
m4.metric("🏆 იაფი აფთიაქი", cheapest)

st.divider()

# ════════════════════════════════════════════════════════════
# TABS SYSTEM
# ════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["📊 ანალიტიკა & გრაფიკები", "⚔️ SKU შედარების მატრიცა", "📋 სრული კატალოგი"])

with tab1:
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("📊 საშუალო ფასი კატეგორიების მიხედვით")
        avg_cat = df.groupby([COL_CATEGORY, COL_SOURCE])[COL_PRICE].mean().reset_index()
        fig1 = px.bar(
            avg_cat, x=COL_CATEGORY, y=COL_PRICE, color=COL_SOURCE,
            barmode="group", text_auto=".2f",
            color_discrete_map={"PSP": "#4f46e5", "Aversi": "#10b981", "GPC": "#f97316"}
        )
        fig1.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=380)
        st.plotly_chart(fig1, use_container_width=True)

    with col_g2:
        st.subheader("🏷 ფასების განაწილება ბრენდების მიხედვით")
        fig2 = px.box(
            df, x=COL_BRAND, y=COL_PRICE, color=COL_SOURCE,
            color_discrete_map={"PSP": "#4f46e5", "Aversi": "#10b981", "GPC": "#f97316"}
        )
        fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=380)
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("⚔️ იდენტური პროდუქტების შედარება")
    mat = get_sku_matrix(df)
    src_cols = [c for c in ["PSP", "Aversi", "GPC"] if c in mat.columns]
    
    if not mat.empty and len(src_cols) >= 2:
        cols_to_show = [COL_NAME] + src_cols + ["სხვაობა (₾)", "სხვაობა (%)", "იაფი წყარო"]
        st.dataframe(
            mat[cols_to_show].style.format({c: "₾{:.2f}" for c in src_cols + ["სხვაობა (₾)"]}),
            use_container_width=True,
            hide_index=True,
            height=450
        )
    else:
        st.info("შედარებისთვის საჭიროა მინიმუმ 2 აფთიაქის მონაცემები.")

with tab3:
    st.subheader("📋 რეესტრი")
    st.dataframe(
        df[[COL_NAME, COL_BRAND, COL_CATEGORY, COL_SOURCE, COL_PRICE, COL_URL]],
        column_config={COL_URL: st.column_config.LinkColumn("ბმული")},
        use_container_width=True,
        hide_index=True
    )
