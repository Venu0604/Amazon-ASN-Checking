"""
Streamlit dashboard: paste an Amazon.in hidden-keywords search URL and see
which ASINs from that URL don't show up in the search results.

Usage:
    source .venv/bin/activate
    pip install streamlit
    streamlit run dashboard.py
"""

import subprocess
import sys

import pandas as pd
import streamlit as st

from checker import run_check

st.set_page_config(page_title="Amazon ASIN Missing Checker", page_icon="🔍", layout="wide")


@st.cache_resource
def _ensure_chromium_installed():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    return True


_ensure_chromium_installed()

st.markdown(
    """
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3, p, label, span, div { color: #12172b; }

    .hero {
        background: linear-gradient(135deg, #eef2fb 0%, #dfe9ff 100%);
        border: 1px solid #d7e0f7;
        border-radius: 14px;
        padding: 28px 32px;
        margin-bottom: 24px;
    }
    .hero h1 { margin: 0 0 6px 0; font-size: 1.9rem; color: #12172b; }
    .hero p { margin: 0; color: #3a4260; font-size: 1rem; }

    div[data-testid="stMetric"] {
        background-color: #f6f8fe;
        border: 1px solid #e2e8f7;
        border-radius: 12px;
        padding: 16px 18px;
    }
    div[data-testid="stMetricValue"] { color: #12172b; }
    div[data-testid="stMetricLabel"] { color: #5b6480; }

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🔍 Amazon ASIN Missing Checker</h1>
        <p>Paste an Amazon.in hidden-keywords search URL and see which ASINs don't show up in the search results.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

url = st.text_area(
    "Search URL",
    placeholder="https://www.amazon.in/s?hidden-keywords=B0..|B0..&tag=...",
    label_visibility="collapsed",
    height=150,
)
run = st.button("Check", type="primary", width="stretch")

if run and not url.strip():
    st.warning("Paste a search URL first.")
elif run:
    status = st.empty()
    log_lines = []

    def on_progress(msg):
        log_lines.append(msg)
        status.info("\n\n".join(log_lines))

    try:
        with st.spinner("Opening browser and reading search results..."):
            result = run_check(url.strip(), on_progress=on_progress)
    except Exception as e:
        st.error(f"Failed to check URL: {e}")
        st.stop()

    status.empty()

    asins = result["asins"]
    present = result["present"]
    missing = result["missing"]
    found = result["found"]

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Requested", len(asins))
    col2.metric("Present", len(present))
    col3.metric("Missing", len(missing))

    df = pd.DataFrame(
        [{"asin": a, "status": "present" if a in found else "missing"} for a in asins]
    )

    def style_status(row):
        color = "#e6f7ec" if row["status"] == "present" else "#fdeaea"
        text_color = "#12172b"
        return [f"background-color: {color}; color: {text_color}"] * len(row)

    if missing:
        st.subheader(f"Missing ASINs ({len(missing)})")
        missing_df = df[df["status"] == "missing"]
        st.dataframe(missing_df.style.apply(style_status, axis=1), width="stretch", hide_index=True)
    else:
        st.success("All ASINs are present in the search results.")

    with st.expander("Full results (present + missing)"):
        st.dataframe(df.style.apply(style_status, axis=1), width="stretch", hide_index=True)

    st.download_button(
        "Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="missing_asins.csv",
        mime="text/csv",
    )
