"""
ბავშვის პროდუქტების ფასების ინდექსი — PSP · Aversi · GEPHA/GPC
გაშვება: streamlit run app.py
"""

from __future__ import annotations

from datetime import datetime

import sys

import pandas as pd
import plotly.express as px
import streamlit as st

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
st.set_page_config(
    page_title="ბავშვის პროდუქტების ფასების ინდექსი",
    page_icon="🍼",
    layout="wide",
)

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

try:
    from aversi import scrape_aversi
    from gpc import scrape_gpc
    from psp import scrape_psp
    from common import normalize_key
except Exception as _import_err:
    st.error("პროგრამის ფაილები ვერ ჩაიტვირთა (scrapers/config).")
    st.code(str(_import_err))
    st.info(
        "გადაწყვეტა:\n"
        "1. გახსენით საქაღალდე `baby-price-index`\n"
        "2. გაუშვით `setup.bat`\n"
        "3. გაუშვით `run.bat` (არა ორმაგი დაწკაპუნება app.py-ზე)"
    )
    st.stop()


def load_all_data(
    sources: list[str],
    max_psp: int,
    max_gpc: int,
    max_aversi: int,
) -> tuple[pd.DataFrame, dict[str, str]]:
    rows: list[dict] = []
    status: dict[str, str] = {}
    progress = st.progress(0, text="მონაცემები იტვირთება...")
    steps = len(sources)
    step_i = 0

    if "PSP" in sources:
        progress.progress(step_i / max(steps, 1), text="PSP — GraphQL API...")
        try:
            rows.extend(scrape_psp(max_pages=max_psp))
            status["PSP"] = "ok"
        except Exception as exc:
            status["PSP"] = str(exc)
        step_i += 1

    if "GEPHA/GPC" in sources:
        progress.progress(step_i / max(steps, 1), text="GPC — კატალოგის გვერდები...")
        try:
            rows.extend(scrape_gpc(max_pages=max_gpc))
            status["GEPHA/GPC"] = "ok"
        except Exception as exc:
            status["GEPHA/GPC"] = str(exc)
        step_i += 1

    if "Aversi" in sources:
        progress.progress(step_i / max(steps, 1), text="Aversi — გვერდები (შეიძლება ნელი იყოს)...")
        try:
            rows.extend(scrape_aversi(max_pages=max_aversi))
            status["Aversi"] = "ok"
        except Exception as exc:
            status["Aversi"] = str(exc)
        step_i += 1

    progress.empty()

    if not rows:
        return pd.DataFrame(), status

    df = pd.DataFrame(rows)
    df["შედარების გასაღები"] = df[COL_NAME].map(normalize_key)
    df[COL_UPDATED] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return df, status


# —— UI ——
st.title("🍼 ბავშვის პროდუქტების ფასების ინდექსი")
st.markdown("**PSP · Aversi · GEPHA/GPC**")

if "df" not in st.session_state:
    st.session_state.df = None
    st.session_state.status = {}
    st.session_state.loaded = False

with st.sidebar:
    st.header("⚙️ პარამეტრები")
    st.caption("ჯერ დააჭირეთ «მონაცემების ჩატვირთვა» — მაშინ დაიწყება სკანირება.")

    sources = st.multiselect(
        "წყაროები",
        ["PSP", "Aversi", "GEPHA/GPC"],
        default=["PSP", "GEPHA/GPC"],
    )
    st.divider()
    st.subheader("პაგინაციის ლიმიტი")
    max_psp = st.slider("PSP მაქს. გვერდი", 1, MAX_PAGES_PSP, 3)
    max_gpc = st.slider("GPC მაქს. გვერდი", 1, MAX_PAGES_GPC, 2)
    max_aversi = st.slider("Aversi მაქს. გვერდი", 1, MAX_PAGES_AVERSI, 2)

    st.divider()
    load_clicked = st.button("📥 მონაცემების ჩატვირთვა", type="primary", use_container_width=True)
    if st.button("🔄 გასუფთავება", use_container_width=True):
        st.session_state.df = None
        st.session_state.status = {}
        st.session_state.loaded = False
        st.rerun()

    st.divider()
    st.markdown("**ბმულები:**")
    st.markdown(f"[PSP]({PSP_CATEGORY_URL})")
    st.markdown(f"[GPC]({GPC_LIST_URL})")
    st.markdown(f"[Aversi]({AVERSI_LIST_URL})")

if load_clicked and sources:
    with st.spinner("მონაცემები იკრიბება — არ დახუროთ ბრაუზერი..."):
        df_new, status_new = load_all_data(sources, max_psp, max_gpc, max_aversi)
    st.session_state.df = df_new
    st.session_state.status = status_new
    st.session_state.loaded = True
    st.rerun()

if not st.session_state.loaded:
    st.info(
        "👋 აპლიკაცია მუშაობს.\n\n"
        "**რა უნდა გააკეთოთ:**\n"
        "1. მარცხნივ აირჩიეთ წყაროები\n"
        "2. დააჭირეთ **«მონაცემების ჩატვირთვა»**\n"
        "3. დაელოდეთ 30 წამიდან 5 წუთამდე (Aversi ყველაზე ნელია)\n\n"
        "თუ ეკრანი ცარიელია — გახსენით: http://localhost:8501"
    )
    with st.expander("❓ ხშირი პრობლემები"):
        st.markdown(
            """
- **`streamlit` არ მოიძებნება** → გაუშვით `setup.bat`, შემდეგ `run.bat`
- **არა `app.py` ორმაცი დაწკაპუნება** → მხოლოდ `run.bat`
- **Aversi ვერ მუშაობს** → გამორთეთ Aversi ან: `playwright install chromium`
- **ყველაფერი ❌** → შეამოწმეთ ინტერნეტი; ტესტისთვის მხოლოდ PSP + 2 გვერდი
            """
        )
    if not sources:
        st.warning("აირჩიეთ მინიმუმ ერთი წყარო, შემდეგ «მონაცემების ჩატვირთვა».")
    st.stop()

df = st.session_state.df
status = st.session_state.status

for src, msg in status.items():
    if msg == "ok":
        n = len(df[df[COL_SOURCE] == src]) if df is not None and len(df) else 0
        st.success(f"✅ {src}: {n} პროდუქტი")
    else:
        st.error(f"❌ {src}: {msg}")

if df is None or getattr(df, "empty", True):
    st.error(
        "მონაცემი ვერ მოიძებნა. სცადეთ მხოლოდ **PSP** (2–3 გვერდი) ან გაზარდეთ გვერდების რაოდენობა."
    )
    st.stop()

st.caption(f"🕐 განახლდა: {df[COL_UPDATED].iloc[0]}")
st.divider()

# KPI
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

# ფილტრები
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
filtered = df[
    df[COL_SOURCE].isin(src_filter)
    & df[COL_PRICE].between(price_range[0], price_range[1])
]
if search.strip():
    filtered = filtered[filtered[COL_NAME].str.contains(search.strip(), case=False, na=False)]

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 საშუალო ფასი", "📈 განაწილება", "📋 ცხრილი", "💡 შედარება"]
)

with tab1:
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

with tab2:
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
    fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=450, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    show_cols = [COL_NAME, COL_PRICE, COL_SOURCE, COL_URL]
    if COL_OLD_PRICE in filtered.columns:
        show_cols.insert(2, COL_OLD_PRICE)
    st.dataframe(
        filtered[show_cols].sort_values(COL_PRICE).reset_index(drop=True),
        use_container_width=True,
        height=450,
        column_config={COL_URL: st.column_config.LinkColumn("ბმული")},
    )
    st.download_button(
        "⬇️ CSV",
        filtered.to_csv(index=False, encoding="utf-8-sig"),
        file_name="baby_price_index.csv",
        mime="text/csv",
    )

with tab4:
    st.caption(
        "შედარება ხდება ნორმალიზებული სახელის მიხედვით. "
        "სრულად იდენტური პროდუქტები სამივე მაღაზიაში იშვიათია — "
        "გამოიყენეთ SKU/ბმული დასაზუსტებლად."
    )
    pivot = (
        filtered.groupby(["შედარების გასაღები", COL_SOURCE])[COL_PRICE]
        .min()
        .unstack(COL_SOURCE)
        .reset_index()
    )
    avail = [c for c in ["PSP", "Aversi", "GEPHA/GPC"] if c in pivot.columns]
    if len(avail) >= 2:
        pivot["მაქს-მინ სხვაობა (₾)"] = pivot[avail].max(axis=1) - pivot[avail].min(axis=1)
        pivot["იაპი წყარო"] = pivot[avail].idxmin(axis=1)
        name_map = filtered.drop_duplicates("შედარების გასაღები").set_index("შედარების გასაღები")[COL_NAME]
        pivot[COL_NAME] = pivot["შედარების გასაღები"].map(name_map)
        show = [COL_NAME] + avail + ["მაქს-მინ სხვაობა (₾)", "იაპი წყარო"]
        pivot = pivot[show].sort_values("მაქს-მინ სხვაობა (₾)", ascending=False).head(30)
        fmt = {c: "₾{:.2f}" for c in avail + ["მაქს-მინ სხვაობა (₾)"]}
        st.dataframe(pivot.style.format(fmt), use_container_width=True, height=400)
    else:
        st.info("შედარებისთვის საჭიროა მინიმუმ 2 წყარო ერთი და იგივე გასაღებით.")
