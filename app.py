"""
app.py — AI Job Tracker Singapore | Streamlit UI

Run locally:
    streamlit run app.py

Deploy: Streamlit Community Cloud (share.streamlit.io)
"""

import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from agent.pipeline import run_pipeline
from profile import DEFAULT_PROFILE

load_dotenv()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Job Tracker — Singapore",
    page_icon="🤖",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("⚙️ Settings")

    st.subheader("🧠 Your Profile")
    profile = st.text_area(
        "Edit your skills & preferences",
        value=DEFAULT_PROFILE,
        height=300,
        help="The AI agent scores every job against this profile. Edit it to update your matches.",
    )

    st.divider()

    st.subheader("🔑 API Keys")
    anthropic_key = st.text_input("Anthropic API Key", type="password",
                                   value=os.getenv("ANTHROPIC_API_KEY", ""),
                                   help="console.anthropic.com — required for scoring")
    serpapi_key = st.text_input("SerpAPI Key", type="password",
                                 value=os.getenv("SERPAPI_KEY", ""),
                                 help="serpapi.com — free tier, captures LinkedIn/Indeed/Glassdoor via Google Jobs")
    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    if serpapi_key:
        os.environ["SERPAPI_KEY"] = serpapi_key

    st.divider()

    st.subheader("🔍 Filters")
    min_score = st.slider("Minimum match score", min_value=0, max_value=10, value=0)
    sources = st.multiselect(
        "Job sources",
        options=["mycareersfuture", "google_jobs", "remotive"],
        default=["mycareersfuture", "google_jobs", "remotive"],
    )

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🤖 AI Job Tracker — Singapore")
st.caption("Fetches live AI/ML roles, scores them against your profile using Claude, and ranks the best matches.")

col1, col2 = st.columns([3, 1])
with col2:
    run_btn = st.button("🔄 Fetch & Score Jobs", type="primary", use_container_width=True)

if not os.getenv("ANTHROPIC_API_KEY"):
    st.warning("⚠️ No Anthropic API key set — jobs will be fetched but scores will all be 0. Add your key in the sidebar.")
if not os.getenv("SERPAPI_KEY"):
    st.info("ℹ️ No SerpAPI key set — LinkedIn/Indeed/Glassdoor results via Google Jobs will be skipped. MyCareersFuture + Remotive will still work.")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "jobs" not in st.session_state:
    st.session_state.jobs = []
if "last_run" not in st.session_state:
    st.session_state.last_run = None

# ---------------------------------------------------------------------------
# Run pipeline
# ---------------------------------------------------------------------------

if run_btn:
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.error("⚠️ Add your Anthropic API key in the sidebar to score jobs.")
    else:
        with st.spinner("Fetching jobs from Remotive & Adzuna... scoring with Claude..."):
            jobs = run_pipeline(profile=profile, min_score=0)
            st.session_state.jobs = jobs
            st.session_state.last_run = datetime.now().strftime("%d %b %Y %H:%M")

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

jobs = st.session_state.jobs

def _score_colour(score: int) -> str:
    if score >= 8:
        return "🟢"
    if score >= 6:
        return "🟡"
    if score >= 4:
        return "🟠"
    return "🔴"


def _render_job_card(job: dict) -> None:
    score = job["match_score"]
    emoji = _score_colour(score)

    with st.container():
        col_score, col_info, col_btn = st.columns([1, 7, 2])

        with col_score:
            st.markdown(f"### {emoji}")
            st.markdown(f"**{score}/10**")

        with col_info:
            st.markdown(f"### {job['title']}")
            st.markdown(f"🏢 **{job['company']}** &nbsp;|&nbsp; 📍 {job['location']} &nbsp;|&nbsp; 💰 {job['salary']}")
            st.caption(f"_{job['match_reason']}_")
            source_labels = {
                "mycareersfuture": "🇸🇬 MyCareersFuture",
                "google_jobs": "🔍 Google Jobs (LinkedIn/Indeed)",
                "remotive": "🌐 Remotive",
            }
            source_badge = source_labels.get(job["source"], job["source"])
            st.caption(source_badge)

            with st.expander("Read full description"):
                st.write(job["description"] or "No description available.")

        with col_btn:
            st.link_button("Apply →", job["url"], use_container_width=True)

        st.divider()


if not jobs:
    st.info("👈 Click **Fetch & Score Jobs** to get started. Remotive works without any API key.")
else:
    # Apply filters
    filtered = [j for j in jobs
                if j["match_score"] >= min_score and j["source"] in sources]

    # Stats row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total fetched", len(jobs))
    m2.metric("After filters", len(filtered))
    top_score = max((j["match_score"] for j in filtered), default=0)
    m3.metric("Top match score", f"{top_score}/10")
    m4.metric("Last refreshed", st.session_state.last_run or "—")

    st.divider()

    if not filtered:
        st.warning("No jobs match your current filters. Try lowering the minimum score.")
    else:
        for job in filtered:
            _render_job_card(job)
