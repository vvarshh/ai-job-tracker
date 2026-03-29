"""
fetchers/serpapi.py — Google Jobs via SerpAPI.
Aggregates LinkedIn, Indeed, Glassdoor, and other job boards via Google Jobs search.
Free tier: 100 searches/month at serpapi.com (no credit card needed).
"""

import os
import requests
from typing import Any

BASE_URL = "https://serpapi.com/search"

SEARCH_TERMS = [
    "AI Engineer Singapore",
    "LLM Engineer Singapore",
    "AI Product Manager Singapore",
    "Machine Learning Engineer Singapore",
    "Generative AI Singapore",
    "AI Agents Developer Singapore",
]


def _fetch(query: str, api_key: str) -> list[dict[str, Any]]:
    try:
        params = {
            "engine": "google_jobs",
            "q": query,
            "location": "Singapore",
            "hl": "en",
            "api_key": api_key,
        }
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("jobs_results", [])
    except Exception:
        return []


def _normalise(job: dict) -> dict[str, Any]:
    # Extract salary from extensions if available
    extensions = job.get("detected_extensions", {})
    salary = extensions.get("salary", "Not specified")
    posted = extensions.get("posted_at", "")

    # Get apply link — prefer direct apply, fall back to first option
    url = ""
    apply_options = job.get("apply_options", [])
    if apply_options:
        url = apply_options[0].get("link", "")

    return {
        "title": job.get("title", ""),
        "company": job.get("company_name", ""),
        "location": job.get("location", "Singapore"),
        "salary": salary,
        "posted": posted,
        "description": job.get("description", "")[:1000],
        "url": url,
        "source": "🔍 Google Jobs",
    }


def fetch_jobs() -> list[dict[str, Any]]:
    """Fetch Singapore AI/ML jobs from Google Jobs via SerpAPI."""
    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        return []  # silently skip if no key configured

    seen_titles_companies: set[str] = set()
    results = []

    for term in SEARCH_TERMS:
        for raw in _fetch(term, api_key):
            # Deduplicate by title + company combo
            dedup_key = f"{raw.get('title', '').lower()}_{raw.get('company_name', '').lower()}"
            if dedup_key not in seen_titles_companies:
                seen_titles_companies.add(dedup_key)
                normalised = _normalise(raw)
                if normalised["title"]:
                    results.append(normalised)

    return results
