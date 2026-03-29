"""
agent/pipeline.py — Fetch and merge jobs from all sources.
"""

import re
from typing import Any

from fetchers import mycareersfuture, remotive, serpapi


def _strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def run_pipeline() -> list[dict[str, Any]]:
    """Fetch jobs from all sources and return merged list."""
    jobs: list[dict] = []
    jobs.extend(mycareersfuture.fetch_jobs())
    jobs.extend(serpapi.fetch_jobs())
    jobs.extend(remotive.fetch_jobs())

    for job in jobs:
        job["description"] = _strip_html(job.get("description", ""))

    return jobs
