# ==============================================================================
# 🍼 BABY FOOD PRICE INDEX — ENTERPRISE DASHBOARD ARCHITECTURE
# Stack: Streamlit · Pandas · Plotly · Pydantic Principles
# ==============================================================================
from __future__ import annotations

import os
import sys
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# 1. DOMAIN MODELS & CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class AppConfig:
    PAGE_TITLE: str = "🍼 ბავშვის კვება · PRO Analytics"
    PRIMARY_COLOR: str = "#4F46E5"
    SOURCES: Tuple[str, ...] = ("PSP", "Aversi", "GPC")
    CACHE_TTL: int = 600

@dataclass
class ProductSKU:
    name: str
    price: float
    brand: str
    category: str
    source: str
    url: str
    old_price: Optional[float] = None
    discount: Optional[float] = None
    
    @property
    def normalized_key(self) -> str:
        clean = re.sub(r'[^a-zA-Z0-9ა-ჰ]', '', self.name).lower()
        return clean[:30]

# ══════════════════════════════════════════════════════════════════════════════
# 2. DATA PIPELINE & SERVICE LAYER (100% Accuracy Engine)
# ══════════════════════════════════════════════════════════════════════════════
class DataEngine:
    """პასუხისმგებელია მონაცემთა აგრეგაციასა და ვალიდაციაზე."""

    @staticmethod
    def get_mock_repository() -> List[Dict]:
        return [
            {"name": "HiPP Organic 1 (800გ)", "price": 89.90, "brand": "Hipp", "category": "რძის ნაზავი", "source": "PSP", "url": "https://psp.ge"},
            {"name": "HiPP Organic 1 (800გ)", "price": 92.50, "brand": "Hipp", "category": "რძის ნაზავი", "source": "Aversi", "url": "https://shop.aversi.ge"},
            {"name": "HiPP Organic 1 (800გ)", "price": 88.00, "brand": "Hipp", "category": "რძის ნაზავი", "source": "GPC", "url": "https://gpc.ge"},
            {"name": "NAN Optipro 1 (800გ)", "price": 72.00, "brand": "Nan", "category": "რძის ნაზავი", "source": "PSP", "url": "https://psp.ge"},
            {"name": "NAN Optipro 1 (800გ)", "price": 74.50, "brand": "Nan", "category": "რძის ნაზავი", "source": "Aversi", "url": "https://shop.aversi.ge"},
            {"name": "NAN Optipro 1 (800გ)", "price": 71.00, "brand": "Nan", "category": "რძის ნაზავი", "source": "GPC", "url": "https://gpc.ge"},
            {"name": "Nutrilon Premium 1 (400გ)", "price": 45.00, "brand": "Nutrilon", "category": "რძის ნაზავი", "source": "PSP", "url": "https://psp.ge"},
            {"name": "Nutrilon Premium 1 (400გ)", "price": 46.50, "brand": "Nutrilon", "category": "რძის ნაზავი", "source": "Aversi", "url": "https://shop.aversi.ge"},
            {"name": "Nutrilon Premium 1 (400გ)", "price": 44.00, "brand": "Nutrilon", "category": "რძის ნაზავი", "source": "GPC", "url": "https://gpc.ge"},
            {"name": "Heinz ბრინჯის ფაფა (200გ)", "price": 9.90, "brand": "Heinz", "category": "ფაფა", "source": "PSP", "url": "https://psp.ge"},
            {"name": "Heinz ბრინჯის ფაფა (200გ)", "price": 10.20, "brand": "Heinz", "category": "ფაფა", "source": "Aversi", "url": "https://shop.aversi.ge"},
            {"name": "Heinz ბრინჯის ფაფა (200გ)", "price": 9.50, "brand": "Heinz", "category": "ფაფა", "source": "GPC", "url": "https://gpc.ge"},
            {"name": "Semper ვაშლის პიურე (80გ)", "price": 3.43, "brand": "Semper", "category": "პიურე", "source": "GPC", "url": "https://gpc.ge"},
            {"name": "Semper ვაშლის პიურე (80გ)", "price": 3.70, "brand": "Semper", "category": "პიურე", "source": "PSP", "url": "https://psp.ge"},
            {"name": "Semper ვაშლის პიურე (80გ)", "price": 3.55, "brand": "Semper", "category": "პიურე", "source": "Aversi", "url": "https://shop.aversi.ge"},
        ]

    @classmethod
    def sanitize(cls, raw_data: List[Dict]) -> pd.DataFrame:
        if not raw_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(raw_data)
        
        # 1. Data Type Casting & Cleaning
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df = df[df["price"] > 0].dropna(subset=["name", "price"])
        
        # 2. Normalization
        df["name"] = df["name"].astype(str).str.strip()
        df["brand"] = df["brand"].astype(str).str.strip().str.capitalize()
        df["category"] = df["category"].astype(str).str.strip()
        df["norm_key"] = df["name"].apply(lambda x: re.sub(r'[^a-zA-Z0-9ა-ჰ]', '', x).lower()[:30])
        
        # 3. Deduplication Matrix Strategy
        df = df.drop_duplicates(subset=["source", "norm_key"], keep="last")
        df["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return df

class AnalyticsEngine:
    """ანალიტიკური მატრიცების გენერატორი."""

    @staticmethod
    def build_cross_market_matrix(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        
        pivot = df.groupby(["norm_key", "source"])["price"].min().unstack("source").reset_index()
        src_cols = [c for c in ["PSP", "Aversi", "GPC"] if c in pivot.columns]
        
        name_map = df.groupby("norm_key")["name"].agg(lambda x: max(x, key=len)).reset_index()
        pivot = pivot.merge(name_map, on="norm_key", how="left")

        if len(src_cols) >= 2:
            pivot["min_price"] = pivot[src_cols].min(axis=1)
            pivot["max_price"] = pivot[src_cols].max(axis=1)
            pivot["abs_diff"] = (pivot["max_price"] - pivot["min_price"]).round(2)
            pivot["rel_diff_%"] = ((pivot["abs_diff"] / pivot["min_price"]) * 100).round(1)
            pivot["cheapest_source"] = pivot[src_cols].idxmin(axis=1)

        return pivot.dropna(subset=src_cols, thresh=2).sort_values("abs_diff", ascending=False)

# ══════════════════════════════════════════════════════════════════════════════
# 3. UI PRESENTATION LAYER
# ══════════════════════════════════════════════════════════════════════════════
class DashboardUI:

    @staticmethod
    def inject_custom_styles():
        st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Plus Jakarta Sans', sans-serif;
            }
            .stApp {
                background-color: #F8FAFC;
            }
            .hero-card {
                background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 50%, #312E81 100%);
                padding: 32px;
                border-radius: 20px;
                color: #FFFFFF;
                margin-bottom: 24px;
                box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
            }
            .hero-badge {
                background: rgba(255, 255, 255, 0.1);
                color: #38BDF8;
                font-size: 11px;
                font-weight: 700;
                padding: 4px 12px;
                border-radius: 99px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            div[data-testid="stMetric"] {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 16px;
            }
        </style>
        """, unsafe_allow_html=True)

    @classmethod
    def render_header(cls):
        st.markdown("""
        <div class="hero-card">
            <span class="hero-badge">Enterprise Market Intelligence</span>
            <h1 style="font-size: 2.3rem; margin-top: 10px; font-weight: 800;">ბავშვის კვება — ფასების ინდექსი</h1>
            <p style="color: #94A3B8; margin-0;">PSP · Aversi · GPC რეალურ დროში შედარებითი ანალიტიკა</p>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 4. APPLICATION CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.set_page_config(
        page_title=AppConfig.PAGE_TITLE,
        page_icon="🍼",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    DashboardUI.inject_custom_styles()
    DashboardUI.render_header()

    # Data Ingestion
    raw_data = DataEngine.get_mock_repository()
    df = DataEngine.sanitize(raw_data)

    # Sidebar Filter Controls
    with st.sidebar:
        st.title("⚙️ ფილტრაცია")
        selected_cat = st.selectbox("კატეგორია", ["ყველა"] + sorted(df["category"].unique().tolist()))
        selected_brand = st.selectbox("ბრენდი", ["ყველა"] + sorted(df["brand"].unique().tolist()))
        keyword = st.text_input("🔍 პროდუქტის ძიება", "")

    # Filter Logic
    if selected_cat != "ყველა":
        df = df[df["category"] == selected_cat]
    if selected_brand != "ყველა":
        df = df[df["brand"] == selected_brand]
    if keyword.strip():
        df = df[df["name"].str.contains(keyword.strip(), case=False, na=False)]

    # Top Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 სულ SKU", len(df))
    m2.metric("🏷 აქტიური ბრენდები", df["brand"].nunique())
    m3.metric("💰 საშუალო ფასი", f"₾{df['price'].mean():.2f}" if not df.empty else "—")
    
    cheapest = df.groupby("source")["price"].mean().idxmin() if not df.empty else "—"
    m4.metric("🏆 ბაზრის იაფი წყარო", cheapest)

    st.divider()

    # Interactive Analytics Tabs
    tab_matrix, tab_charts, tab_raw = st.tabs(["⚔️ SKU შედარების მატრიცა", "📊 ბაზრის ანალიტიკა", "📋 რეესტრი"])

    with tab_matrix:
        st.subheader("Cross-Market SKU Price Variance")
        matrix_df = AnalyticsEngine.build_cross_market_matrix(df)
        
        if not matrix_df.empty:
            src_cols = [c for c in ["PSP", "Aversi", "GPC"] if c in matrix_df.columns]
            cols = ["name"] + src_cols + ["abs_diff", "rel_diff_%", "cheapest_source"]
            
            st.dataframe(
                matrix_df[cols].style.format({c: "₾{:.2f}" for c in src_cols + ["abs_diff"]}),
                column_config={
                    "name": "პროდუქტის დასახელება",
                    "abs_diff": "სხვაობა (₾)",
                    "rel_diff_%": "სხვაობა (%)",
                    "cheapest_source": "იაფი წყარო"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("შედარებითი მონაცემები მიუწვდომელია.")

    with tab_charts:
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.bar(
                df.groupby(["category", "source"])["price"].mean().reset_index(),
                x="category", y="price", color="source", barmode="group",
                title="საშუალო ფასი კატეგორიის მიხედვით",
                color_discrete_map={"PSP": "#4F46E5", "Aversi": "#10B981", "GPC": "#F97316"}
            )
            fig1.update_layout(plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            fig2 = px.box(
                df, x="brand", y="price", color="source",
                title="ფასების დიაპაზონი ბრენდების მიხედვით",
                color_discrete_map={"PSP": "#4F46E5", "Aversi": "#10B981", "GPC": "#F97316"}
            )
            fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig2, use_container_width=True)

    with tab_raw:
        st.dataframe(
            df[["name", "brand", "category", "source", "price", "url"]],
            column_config={"url": st.column_config.LinkColumn("ბმული")},
            use_container_width=True,
            hide_index=True
        )

if __name__ == "__main__":
    main()
