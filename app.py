"""
app.py — AI Job Tracker Singapore | Streamlit UI
"""

import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from agent.pipeline import run_pipeline

load_dotenv()

st.set_page_config(
    page_title="AI Job Tracker — Singapore",
    page_icon="🤖",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🤖 AI Job Tracker")
    st.caption("Singapore AI/ML roles — live from MyCareersFuture, Google Jobs & Remotive")

    st.divider()

    st.subheader("🔑 API Keys")
    serpapi_key = st.text_input(
        "SerpAPI Key",
        type="password",
        value=os.getenv("SERPAPI_KEY", ""),
        help="serpapi.com — free tier, pulls LinkedIn/Indeed/Glassdoor via Google Jobs",
    )
    if serpapi_key:
        os.environ["SERPAPI_KEY"] = serpapi_key

    st.divider()

    st.subheader("🔍 Search & Filter")
    keyword = st.text_input("Search roles", placeholder="e.g. LLM, agent, product...")
    sources = st.multiselect(
        "Sources",
        options=["🇸🇬 MyCareersFuture", "🔍 Google Jobs", "🌐 Remotive"],
        default=["🇸🇬 MyCareersFuture", "🔍 Google Jobs", "🌐 Remotive"],
    )

    st.divider()
    st.subheader("↕️ Sort by")
    sort_col = st.selectbox("Column", ["posted", "title", "company", "salary"])
    sort_asc = st.radio("Order", ["Newest first", "A → Z"], index=0) == "A → Z"

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🤖 AI Job Tracker — Singapore")
st.caption("Live AI/ML roles pulled from MyCareersFuture, Google Jobs (LinkedIn/Indeed), and Remotive.")

col1, col2 = st.columns([4, 1])
with col2:
    run_btn = st.button("🔄 Fetch Jobs", type="primary", use_container_width=True)

if not os.getenv("SERPAPI_KEY"):
    st.info("ℹ️ No SerpAPI key — Google Jobs (LinkedIn/Indeed) will be skipped. MyCareersFuture + Remotive still work without any key.")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "jobs" not in st.session_state:
    st.session_state.jobs = []
if "last_run" not in st.session_state:
    st.session_state.last_run = None

# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

if run_btn:
    with st.spinner("Fetching jobs..."):
        st.session_state.jobs = run_pipeline()
        st.session_state.last_run = datetime.now().strftime("%d %b %Y %H:%M")

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

jobs = st.session_state.jobs

if not jobs:
    st.info("👈 Click **Fetch Jobs** to load live roles.")
else:
    # Filter
    filtered = jobs
    if keyword:
        kw = keyword.lower()
        filtered = [
            j for j in filtered
            if kw in j["title"].lower()
            or kw in j["company"].lower()
            or kw in j["description"].lower()
        ]
    if sources:
        filtered = [j for j in filtered if j["source"] in sources]

    # Sort
    reverse = not sort_asc
    if sort_col == "posted":
        filtered = sorted(filtered, key=lambda j: j.get("posted", ""), reverse=reverse)
    else:
        filtered = sorted(filtered, key=lambda j: (j.get(sort_col) or "").lower(), reverse=reverse)

    # Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Total fetched", len(jobs))
    c2.metric("Showing", len(filtered))
    c3.metric("Last refreshed", st.session_state.last_run or "—")

    st.divider()

    if not filtered:
        st.warning("No results match your filters. Try a different keyword or source.")
    else:
        # Table header
        h1, h2, h3, h4, h5, h6 = st.columns([3, 2, 1.5, 1.2, 1, 1])
        h1.markdown("**Role**")
        h2.markdown("**Company**")
        h3.markdown("**Salary**")
        h4.markdown("**Posted**")
        h5.markdown("**Source**")
        h6.markdown("")
        st.divider()

        for job in filtered:
            c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1.5, 1.2, 1, 1])
            with c1:
                with st.expander(job["title"] or "—"):
                    st.write(job["description"] or "No description available.")
            c2.write(job["company"] or "—")
            c3.write(job["salary"] or "—")
            c4.write(job["posted"] or "—")
            c5.write(job["source"])
            with c6:
                if job.get("url"):
                    st.link_button("Apply →", job["url"], use_container_width=True)
