"""
fetchers/remotive.py — Fetch remote AI/ML jobs from Remotive API.
No API key required. Covers remote roles open to Singapore candidates.
"""

import requests
from typing import Any

BASE_URL = "https://remotive.com/api/remote-jobs"
SEARCH_TERMS = ["ai engineer", "ai product manager", "ai agents", "llm engineer", "machine learning engineer"]


def _fetch(search: str) -> list[dict[str, Any]]:
    try:
        resp = requests.get(BASE_URL, params={"search": search}, timeout=10)
        resp.raise_for_status()
        return resp.json().get("jobs", [])
    except Exception:
        return []


def _normalise(job: dict) -> dict[str, Any]:
    return {
        "title": job.get("title", ""),
        "company": job.get("company_name", ""),
        "location": job.get("candidate_required_location") or "Remote",
        "salary": job.get("salary") or "Not specified",
        "posted": job.get("publication_date", "")[:10],
        "description": _strip_html(job.get("description", ""))[:1000],
        "url": job.get("url", ""),
        "source": "🌐 Remotive",
    }


def _strip_html(text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", " ", text).strip()


def fetch_jobs() -> list[dict[str, Any]]:
    """Fetch and deduplicate remote AI/ML jobs from Remotive."""
    seen_urls: set[str] = set()
    results = []

    for term in SEARCH_TERMS:
        for raw in _fetch(term):
            url = raw.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                results.append(_normalise(raw))

    return results
