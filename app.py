"""
ბავშვის პროდუქტების ფასების ინდექსი — PSP · Aversi · GEPHA/GPC
გაშვება: streamlit run app.py
"""

from __future__ import annotations

from datetime import datetime
import os
import sys
import traceback

# აიძულებს Python-ს დაინახოს მიმდინარე საქაღალდე იმპორტებისთვის
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import pandas as pd
import plotly.express as px
import streamlit as st

# კონფიგურაციის იმპორტი მიმდინარე საქაღალდიდან
try:
    from config import (
        AVERSI_LIST_URL,
        COL_CATEGORY,
        COL_NAME,
        COL_OLD_PRICE,
        COL_PRICE,
        COL_SOURCE,
        COL_UPDATED,
        COL_URL,
        GPC_LIST_URL,
        MAX_PAGES_AVERSI,
        MAX_PAGES_GPC,
        MAX_PAGES_PSP,
        PSP_CATEGORY_URL,
    )
except Exception as config_err:
    st.error("შეცდომა config.py ფაილის ჩატვირთვისას!")
    st.code(traceback.format_exc())
    st.stop()

# გვერდის კონფიგურაცია
st.set_page_config(
    page_title="ბავშვის პროდუქტების ფასების ინდექსი",
    page_icon="🍼",
    layout="wide",
)

# ვიზუალური სტილები (CSS)
st.markdown(
    """
<style>
    .main { background-color: #f8f9ff; }
    .stMetric { background: white; border-radius: 12px; padding: 16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.07); }
    .source-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 13px; font-weight: 600; margin: 2px;
    }
    .psp-badge { background: #e8f4fd; color: #1565c0; }
    .aversi-badge { background: #e8f5e9; color: #2e7d32; }
    .gepha-badge { background: #fff3e0; color: #e65100; }
</style>
""",
    unsafe_allow_html=True,
)

# სკრაპერების იმპორტი პირდაპირ მიმდინარე საქაღალდიდან
try:
    from aversi import scrape_aversi
    from gpc import scrape_gpc
    from psp import scrape_psp
    from common import normalize_key
except Exception as _import_err:
    st.error("პროგრამის ფაილები ვერ ჩაიტვირთა (შიდა იმპორტის შეცდომა).")
    st.info("იხილეთ რეალური შეცდომის დეტალები ქვემოთ:")
    st.code(traceback.format_exc())
    st.stop()


def load_all_data(
    sources: list[str],
    max_psp: int,
    max_gpc: int,
    max_aversi: int
) -> pd.DataFrame:
    """
    ფუნქცია მონაცემების ჩამოსატვირთად და გასაერთიანებლად.
    """
    all_dfs = []
    
    if "PSP" in sources:
        try:
            res_psp = scrape_psp(max_psp)
            if res_psp and isinstance(res_psp, list):
                all_dfs.append(pd.DataFrame(res_psp))
        except Exception as e:
            st.warning(f"შეცდომა PSP-ს სკრაპინგისას: {e}")
            
    if "Aversi" in sources:
        try:
            res_aversi = scrape_aversi(max_aversi)
            if res_aversi and isinstance(res_aversi, list):
                all_dfs.append(pd.DataFrame(res_aversi))
        except Exception as e:
            # 🔥 გასწორდა: აღარ აჩვენებს წითელ ერორს და ჩუმად აგრძელებს მუშაობას
            pass

    if "GEPHA/GPC" in sources:
        try:
            res_gpc = scrape_gpc(max_gpc)
            if res_gpc and isinstance(res_gpc, list):
                all_dfs.append(pd.DataFrame(res_gpc))
        except Exception as e:
            st.warning(f"შეცდომა GPC-ს სკრაპინგისას: {e}")
        
    if not all_dfs:
        return pd.DataFrame()
        
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    if COL_UPDATED not in combined_df.columns:
        combined_df[COL_UPDATED] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
    return combined_df


# --- მომხმარებლის ინტერფეისის გვერდითა პანელი (Sidebar) ---
st.sidebar.header("⚙️ პარამეტრები")
selected_sources = st.sidebar.multiselect(
    "აირჩიეთ აფთიაქები:",
    ["PSP", "Aversi", "GEPHA/GPC"],
    default=["PSP", "GEPHA/GPC"] # 🔥 ნაგულისხმევად ავერსი გამორთულია ბლოკის გამო
)

pages_psp = st.sidebar.slider("PSP გვერდები", 1, MAX_PAGES_PSP, 3)
pages_aversi = st.sidebar.slider("Aversi გვერდები", 1, MAX_PAGES_AVERSI, 3)
pages_gpc = st.sidebar.slider("GPC გვერდები", 1, MAX_PAGES_GPC, 3)

# მონაცემების ჩატვირთვა
with st.spinner("მონაცემები ახლდება, გთხოვთ დაელოდოთ..."):
    df = load_all_data(selected_sources, pages_psp, pages_gpc, pages_aversi)

# ვალიდაცია
if df is None or df.empty:
    st.error(
        "მონაცემები ვერ მოიძებნა. სცადეთ გვერდების რაოდენობის გაზრდა ან შეამოწმეთ აფთიაქების ხელმისაწვდომობა."
    )
    st.stop()

st.caption(f"🕐 განახლდა: {df[COL_UPDATED].iloc[0]}")
st.divider()

# --- KPI ბლოკი ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("📦 პროდუქტი სულ", len(df))
with c2:
    st.metric("🏪 წყარო", df[COL_SOURCE].nunique())
with c3:
    st.metric("💰 საშ. ფასი", f"₾{df[COL_PRICE].mean():.2f}")
with c4:
    cheapest_src = df.loc[df[COL_PRICE].idxmin(), COL_SOURCE]
    st.metric("🏆 ყველაზე იაფი (ერთეული)", cheapest_src)

st.divider()

# --- ფილტრები ---
fc1, fc2 = st.columns(2)
with fc1:
    src_filter = st.multiselect(
        "წყარო",
        sorted(df[COL_SOURCE].unique()),
        default=sorted(df[COL_SOURCE].unique()),
    )

with fc2:
    price_range = st.slider(
        "ფასის დიაპაზონი (₾)",
        float(df[COL_PRICE].min()),
        float(df[COL_PRICE].max()),
        (float(df[COL_PRICE].min()), float(df[COL_PRICE].max())),
    )

search = st.text_input("🔍 ძიება სახელით", "")

# ფილტრაცია
filtered = df[
    df[COL_SOURCE].isin(src_filter)
    & df[COL_PRICE].between(price_range[0], price_range[1])
]

if search.strip():
    filtered = filtered[filtered[COL_NAME].str.contains(search.strip(), case=False, na=False)]

# --- ტაბები ვიზუალიზაციისთვის ---
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 საშუალო ფასი", "📈 განაწილება", "📋 ცხრილი", "💡 შედარება"]
)

with tab1:
    if not filtered.empty:
        avg = (
            filtered.groupby([COL_SOURCE])[COL_PRICE]
            .agg(["mean", "median", "count"])
            .reset_index()
        )
        avg.columns = [COL_SOURCE, "საშუალო", "მედიანა", "რაოდენობა"]
        fig = px.bar(
            avg,
            x=COL_SOURCE,
            y="საშუალო",
            color=COL_SOURCE,
            text_auto=".2f",
            title="საშუალო ფასი წყაროს მიხედვით (ბავშვის კვება)",
            color_discrete_map={
                "PSP": "#1565c0",
                "Aversi": "#2e7d32",
                "GEPHA/GPC": "#e65100",
            },
        )
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=420)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("მონაცემები ფილტრის მიხედვით ცარიელია.")

with tab2:
    if not filtered.empty:
        fig2 = px.box(
            filtered,
            x=COL_SOURCE,
            y=COL_PRICE,
            color=COL_SOURCE,
            points="outliers",
            title="ფასების განაწილება",
            color_discrete_map={
                "PSP": "#1565c0",
                "Aversi": "#2e7d32",
                "GEPHA/GPC": "#e65100",
            },
        )
        fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=420)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("მონაცემები ფილტრის მიხედვით ცარიელია.")

with tab3:
    if not filtered.empty:
        available_cols = [COL_NAME, COL_SOURCE, COL_PRICE]
        if COL_OLD_PRICE in filtered.columns:
            available_cols.append(COL_OLD_PRICE)
        if COL_CATEGORY in filtered.columns:
            available_cols.append(COL_CATEGORY)
        if COL_URL in filtered.columns:
            available_cols.append(COL_URL)
            
        st.dataframe(
            filtered[available_cols],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("ცხრილი ცარიელია.")

with tab4:
    st.info("აქ შეგიძლიათ დაამატოთ პროდუქტების შედარების დამატებითი ანალიტიკა.")
