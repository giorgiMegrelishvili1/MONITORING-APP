# ==============================================================================
# 🍼 BABY FOOD PRICE INDEX — DARK EXECUTIVE DASHBOARD
# ==============================================================================
from __future__ import annotations

import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# 1. PAGE SETUP & DARK THEME CSS
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Page: Home · Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #0E1117 !important;
        color: #E2E8F0 !important;
    }
    
    /* Dark Background Override */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161B22 !important;
        border-right: 1px solid #21262D !important;
    }

    /* Top Page Banner */
    .dark-header {
        background-color: #161B22;
        border: 1px solid #21262D;
        border-radius: 8px;
        padding: 12px 20px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .page-title {
        color: #FFFFFF;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0;
    }

    /* KPI Metric Cards Custom Design */
    .kpi-card {
        background: #161B22;
        border: 1px solid #21262D;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .kpi-header {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #8B949E;
        font-size: 0.78rem;
        font-weight: 500;
    }
    .kpi-sub {
        color: #6E7681;
        font-size: 0.7rem;
        margin-top: 4px;
    }
    .kpi-value {
        color: #FFFFFF;
        font-size: 1.4rem;
        font-weight: 700;
        margin-top: 6px;
    }
    
    /* Section Containers */
    .chart-box {
        background: #161B22;
        border: 1px solid #21262D;
        border-radius: 8px;
        padding: 15px;
        margin-top: 15px;
    }

    /* Pill Filter Badges */
    .badge-btn {
        background-color: #E63946;
        color: white;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 5px;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 2. DEMO DATA PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
DEMO_DATA = [
    {"name": "HiPP Organic 1 (800გ)", "price": 89.90, "brand": "Hipp", "category": "რძის ნაზავი", "source": "PSP", "region": "თბილისი", "sales": 2482205},
    {"name": "HiPP Organic 1 (800გ)", "price": 92.50, "brand": "Hipp", "category": "რძის ნაზავი", "source": "Aversi", "region": "ბათუმი", "sales": 847300},
    {"name": "HiPP Organic 1 (800გ)", "price": 88.00, "brand": "Hipp", "category": "რძის ნაზავი", "source": "GPC", "region": "ქუთაისი", "sales": 4964411},
    {"name": "NAN Optipro 1 (800გ)", "price": 72.00, "brand": "Nan", "category": "რძის ნაზავი", "source": "PSP", "region": "რუსთავი", "sales": 2593682},
    {"name": "NAN Optipro 1 (800გ)", "price": 74.50, "brand": "Nan", "category": "რძის ნაზავი", "source": "Aversi", "region": "თბილისი", "sales": 351000},
    {"name": "NAN Optipro 1 (800გ)", "price": 71.00, "brand": "Nan", "category": "რძის ნაზავი", "source": "GPC", "region": "გორის", "sales": 1200000},
    {"name": "Nutrilon Premium 1", "price": 45.00, "brand": "Nutrilon", "category": "რძის ნაზავი", "source": "PSP", "region": "ზუგდიდი", "sales": 890000},
    {"name": "Heinz ფაფა (200გ)", "price": 9.90, "brand": "Heinz", "category": "ფაფა", "source": "PSP", "region": "თბილისი", "sales": 450000},
    {"name": "Semper პიურე (80გ)", "price": 3.43, "brand": "Semper", "category": "პიურე", "source": "GPC", "region": "ბათუმი", "sales": 310000},
]

df = pd.DataFrame(DEMO_DATA)

# ══════════════════════════════════════════════════════════════════════════════
# 3. SIDEBAR (LOGO & MENU)
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <div style="font-size: 2.5rem;">🛑</div>
            <h3 style="color: #E63946; margin: 5px 0 0 0; font-weight: 800;">COMPANY LOGO</h3>
            <p style="color: #6E7681; font-size: 0.7rem;">Developed & Maintained by Demo</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<p style='color: #8B949E; font-size: 0.8rem; font-weight: 600;'>Please Filter</p>", unsafe_allow_html=True)
    
    selected_cat = st.selectbox("Select Category", ["ყველა"] + sorted(df["category"].unique().tolist()))
    selected_brand = st.selectbox("Select Brand", ["ყველა"] + sorted(df["brand"].unique().tolist()))
    
    st.markdown("---")
    st.markdown("<p style='color: #8B949E; font-size: 0.8rem; font-weight: 600;'>💻 Main Menu</p>", unsafe_allow_html=True)
    
    st.button("🔴 Home", use_container_width=True)
    st.button("👁️ Progress", use_container_width=True)

# Apply Filter
if selected_cat != "ყველა":
    df = df[df["category"] == selected_cat]
if selected_brand != "ყველა":
    df = df[df["brand"] == selected_brand]

# ══════════════════════════════════════════════════════════════════════════════
# 4. MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
# Page Header Bar
st.markdown("""
<div class="dark-header">
    <div class="page-title">Page: Home</div>
    <div style="color: #8B949E; font-size: 0.85rem;">📁 My Excel WorkBook</div>
</div>
""", unsafe_allow_html=True)

# KPI Metrics Top Row
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-header">📌 Total Investment</div>
        <div class="kpi-sub">sum 125</div>
        <div class="kpi-value">2,482,205,481</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-header">📌 Most Frequent</div>
        <div class="kpi-sub">mode 125</div>
        <div class="kpi-value">847,300</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-header">📌 Average</div>
        <div class="kpi-sub">average 125</div>
        <div class="kpi-value">4,964,411</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-header">📌 Central Earnings</div>
        <div class="kpi-sub">median 125</div>
        <div class="kpi-value">2,593,682</div>
    </div>
    """, unsafe_allow_html=True)

with k5:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-header">📌 Ratings</div>
        <div class="kpi-sub">Rating</div>
        <div class="kpi-value">3.51K</div>
    </div>
    """, unsafe_allow_html=True)

# Charts Layout (3 Columns like the Image)
c1, c2, c3 = st.columns([1.2, 1.2, 1])

with c1:
    st.markdown("<p style='color: #8B949E; font-size: 0.85rem; font-weight: 600; margin-top: 15px;'>Investment by State</p>", unsafe_allow_html=True)
    fig_line = px.line(
        df, x="region", y="sales",
        markers=True,
        color_discrete_sequence=["#38BDF8"]
    )
    fig_line.update_layout(
        paper_bgcolor="#161B22",
        plot_bgcolor="#161B22",
        font_color="#8B949E",
        margin=dict(l=10, r=10, t=20, b=20),
        height=320,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#21262D")
    )
    st.plotly_chart(fig_line, use_container_width=True)

with c2:
    st.markdown("<p style='color: #8B949E; font-size: 0.85rem; font-weight: 600; margin-top: 15px;'>Investment by Business Type</p>", unsafe_allow_html=True)
    fig_bar = px.bar(
        df, y="brand", x="price", orientation="h",
        color_discrete_sequence=["#0EA5E9"]
    )
    fig_bar.update_layout(
        paper_bgcolor="#161B22",
        plot_bgcolor="#161B22",
        font_color="#8B949E",
        margin=dict(l=10, r=10, t=20, b=20),
        height=320,
        xaxis=dict(showgrid=True, gridcolor="#21262D"),
        yaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with c3:
    st.markdown("<p style='color: #8B949E; font-size: 0.85rem; font-weight: 600; margin-top: 15px;'>Regions by Ratings</p>", unsafe_allow_html=True)
    fig_pie = px.pie(
        df, names="source", values="price",
        color_discrete_sequence=["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]
    )
    fig_pie.update_layout(
        paper_bgcolor="#161B22",
        plot_bgcolor="#161B22",
        font_color="#8B949E",
        margin=dict(l=10, r=10, t=20, b=20),
        height=320,
        showlegend=True
    )
    st.plotly_chart(fig_pie, use_container_width=True)
