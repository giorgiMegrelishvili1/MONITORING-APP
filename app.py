# ==============================================================================
# 🍼 BABY FOOD PRICE INDEX — PERFECTED DARK DASHBOARD
# ==============================================================================
from __future__ import annotations

import re
import pandas as pd
import plotly.express as px
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# 1. PAGE SETUP & PERFECTED CSS
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Executive Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
    }
    
    .stApp {
        background-color: #0B0E14;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #121721 !important;
        border-right: 1px solid #1E2636 !important;
    }

    .dark-header {
        background-color: #121721;
        border: 1px solid #1E2636;
        border-radius: 10px;
        padding: 14px 22px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .page-title {
        color: #FFFFFF;
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0;
    }

    /* Fixed KPI Cards */
    .kpi-card {
        background: #121721;
        border: 1px solid #1E2636;
        border-radius: 10px;
        padding: 16px 18px;
        height: 100%;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .kpi-header {
        color: #94A3B8;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-sub {
        color: #64748B;
        font-size: 0.7rem;
        margin-top: 2px;
    }
    .kpi-value {
        color: #FFFFFF;
        font-size: 1.45rem;
        font-weight: 800;
        margin-top: 8px;
        white-space: nowrap;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 2. HELPER FOR NUMBER FORMATTING (PREVENTS OVERFLOW)
# ══════════════════════════════════════════════════════════════════════════════
def format_num(val: float) -> str:
    if val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.2f}B"
    if val >= 1_000_000:
        return f"{val / 1_000_000:.2f}M"
    if val >= 1_000:
        return f"{val / 1_000:.1f}K"
    return str(val)

# Data
DEMO_DATA = [
    {"name": "HiPP Organic 1", "price": 89.90, "brand": "Hipp", "category": "რძის ნაზავი", "source": "PSP", "region": "თბილისი", "sales": 2482205481},
    {"name": "HiPP Organic 1", "price": 92.50, "brand": "Hipp", "category": "რძის ნაზავი", "source": "Aversi", "region": "ბათუმი", "sales": 847300},
    {"name": "HiPP Organic 1", "price": 88.00, "brand": "Hipp", "category": "რძის ნაზავი", "source": "GPC", "region": "ქუთაისი", "sales": 4964411},
    {"name": "NAN Optipro 1", "price": 72.00, "brand": "Nan", "category": "რძის ნაზავი", "source": "PSP", "region": "რუსთავი", "sales": 2593682},
    {"name": "NAN Optipro 1", "price": 74.50, "brand": "Nan", "category": "რძის ნაზავი", "source": "Aversi", "region": "თბილისი", "sales": 3510000},
]
df = pd.DataFrame(DEMO_DATA)

# ══════════════════════════════════════════════════════════════════════════════
# 3. SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <div style="font-size: 2rem;">🛑</div>
            <h3 style="color: #EF4444; margin: 5px 0 0 0; font-weight: 800;">COMPANY LOGO</h3>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    selected_cat = st.selectbox("Select Category", ["ყველა"] + sorted(df["category"].unique().tolist()))
    selected_brand = st.selectbox("Select Brand", ["ყველა"] + sorted(df["brand"].unique().tolist()))

# ══════════════════════════════════════════════════════════════════════════════
# 4. MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="dark-header">
    <div class="page-title">Page: Executive Home</div>
    <div style="color: #64748B; font-size: 0.85rem;">📁 Real-Time Analytics</div>
</div>
""", unsafe_allow_html=True)

# Metric Cards Row
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">📌 Total Investment</div>
        <div class="kpi-sub">sum 125</div>
        <div class="kpi-value">{format_num(2482205481)}</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">📌 Most Frequent</div>
        <div class="kpi-sub">mode 125</div>
        <div class="kpi-value">{format_num(847300)}</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">📌 Average</div>
        <div class="kpi-sub">average 125</div>
        <div class="kpi-value">{format_num(4964411)}</div>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">📌 Central Earnings</div>
        <div class="kpi-sub">median 125</div>
        <div class="kpi-value">{format_num(2593682)}</div>
    </div>""", unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">📌 Ratings</div>
        <div class="kpi-sub">Rating</div>
        <div class="kpi-value">3.51K</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# Charts Layout
c1, c2, c3 = st.columns([1.2, 1.2, 1])

with c1:
    st.markdown("<p style='color: #94A3B8; font-size: 0.85rem; font-weight: 600;'>Investment by State</p>", unsafe_allow_html=True)
    fig_line = px.line(df, x="region", y="sales", markers=True, color_discrete_sequence=["#38BDF8"])
    fig_line.update_layout(
        paper_bgcolor="#121721",
        plot_bgcolor="#121721",
        font_color="#94A3B8",
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        xaxis=dict(showgrid=False, tickangle=-25),
        yaxis=dict(showgrid=True, gridcolor="#1E2636")
    )
    st.plotly_chart(fig_line, use_container_width=True)

with c2:
    st.markdown("<p style='color: #94A3B8; font-size: 0.85rem; font-weight: 600;'>Investment by Business Type</p>", unsafe_allow_html=True)
    fig_bar = px.bar(df, y="brand", x="price", orientation="h", color_discrete_sequence=["#0EA5E9"])
    fig_bar.update_layout(
        paper_bgcolor="#121721",
        plot_bgcolor="#121721",
        font_color="#94A3B8",
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        xaxis=dict(showgrid=True, gridcolor="#1E2636"),
        yaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with c3:
    st.markdown("<p style='color: #94A3B8; font-size: 0.85rem; font-weight: 600;'>Regions by Ratings</p>", unsafe_allow_html=True)
    fig_pie = px.pie(df, names="source", values="price", hole=0.4, color_discrete_sequence=["#3B82F6", "#10B981", "#F59E0B"])
    fig_pie.update_layout(
        paper_bgcolor="#121721",
        plot_bgcolor="#121721",
        font_color="#94A3B8",
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
    )
    st.plotly_chart(fig_pie, use_container_width=True)
