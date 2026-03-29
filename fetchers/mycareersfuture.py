"""
fetchers/mycareersfuture.py — Singapore's official government job portal.
Public API, no key required. Covers the majority of Singapore job listings.
Docs: https://api.mycareersfuture.gov.sg
"""

import requests
from typing import Any

BASE_URL = "https://api.mycareersfuture.gov.sg/v2/search"

SEARCH_TERMS = [
    "ai engineer",
    "machine learning engineer",
    "llm engineer",
    "ai product manager",
    "data scientist ai",
    "generative ai",
    "ai agent",
]


def _fetch(search: str, limit: int = 20) -> list[dict[str, Any]]:
    try:
        params = {
            "search": search,
            "limit": limit,
            "page": 0,
            "sortBy": "new_posting_date",
        }
        headers = {"Content-Type": "application/json"}
        resp = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception:
        return []


def _parse_salary(job: dict) -> str:
    salary = job.get("salary", {})
    if not salary:
        return "Not specified"
    low = salary.get("minimum")
    high = salary.get("maximum")
    if low and high:
        return f"SGD {int(low):,} – {int(high):,}/mo"
    if low:
        return f"SGD {int(low):,}+/mo"
    return "Not specified"


def _normalise(job: dict) -> dict[str, Any]:
    metadata = job.get("metadata", {})
    position = job.get("position", {})
    company = job.get("postedCompany", {})

    posted = job.get("metadata", {}).get("newPostingDate", "") or job.get("metadata", {}).get("originalPostingDate", "")
    posted = posted[:10] if posted else ""

    return {
        "title": position.get("title", ""),
        "company": company.get("name", ""),
        "location": "Singapore",
        "salary": _parse_salary(job),
        "posted": posted,
        "description": job.get("description", "")[:1000],
        "url": f"https://www.mycareersfuture.gov.sg/job/{job.get('uuid', '')}",
        "source": "🇸🇬 MyCareersFuture",
    }


def fetch_jobs() -> list[dict[str, Any]]:
    """Fetch and deduplicate Singapore AI/ML jobs from MyCareersFuture."""
    seen_urls: set[str] = set()
    results = []

    for term in SEARCH_TERMS:
        for raw in _fetch(term):
            url = f"https://www.mycareersfuture.gov.sg/job/{raw.get('uuid', '')}"
            if url and url not in seen_urls:
                seen_urls.add(url)
                normalised = _normalise(raw)
                if normalised["title"]:  # skip empty titles
                    results.append(normalised)

    return results
