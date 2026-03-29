"""
agent/pipeline.py — Fetch → Score → Rank pipeline.

Fetches jobs from all sources, scores them all in ONE Claude API call,
then ranks by score descending.
"""

import json
import os
import re
from typing import Any

import anthropic

from agent.prompts import BATCH_SCORE_PROMPT
from fetchers import mycareersfuture, remotive, serpapi


def _strip_html(text: str) -> str:
    """Remove HTML tags and clean up whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)   # HTML entities like &amp;
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _sanitise(value: Any) -> str:
    """Convert to string and remove problematic characters."""
    s = str(value or "")
    s = s.replace("\x00", "")  # null bytes
    return s.strip()


def fetch_all_jobs() -> list[dict]:
    """Pull and merge jobs from all sources."""
    jobs: list[dict] = []
    jobs.extend(mycareersfuture.fetch_jobs())
    jobs.extend(serpapi.fetch_jobs())
    jobs.extend(remotive.fetch_jobs())

    # Clean descriptions
    for job in jobs:
        job["description"] = _strip_html(_sanitise(job.get("description", "")))

    return jobs


def score_all_jobs(jobs: list[dict], profile: str) -> list[dict]:
    """Score all jobs in a single Claude API call."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        for job in jobs:
            job["match_score"] = 0
            job["match_reason"] = "⚠️ Add Anthropic API key in the sidebar to score jobs."
        return jobs

    # Build compact job list for the prompt
    jobs_text = ""
    for i, job in enumerate(jobs):
        desc = job["description"][:300]
        jobs_text += (
            f"{i+1}. {_sanitise(job['title'])} at {_sanitise(job['company'])} "
            f"({_sanitise(job['location'])}) | {_sanitise(job['salary'])}\n"
            f"   {desc}\n\n"
        )

    prompt = (
        BATCH_SCORE_PROMPT
        .replace("PROFILE_PLACEHOLDER", _sanitise(profile))
        .replace("JOBS_PLACEHOLDER", jobs_text)
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # Strip markdown fences if present
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()

        scores = json.loads(raw)

        for i, job in enumerate(jobs):
            if i < len(scores):
                job["match_score"] = max(0, min(10, int(scores[i].get("score", 0))))
                job["match_reason"] = scores[i].get("reason", "")
            else:
                job["match_score"] = 0
                job["match_reason"] = "Not scored."

    except Exception as e:
        error_msg = str(e)[:120]
        for job in jobs:
            job["match_score"] = 0
            job["match_reason"] = f"Scoring error: {error_msg}"

    return jobs


def run_pipeline(profile: str, min_score: int = 0) -> list[dict]:
    """Run the full pipeline and return ranked, filtered results."""
    jobs = fetch_all_jobs()
    jobs = score_all_jobs(jobs, profile)
    jobs = sorted(jobs, key=lambda j: j["match_score"], reverse=True)
    if min_score > 0:
        jobs = [j for j in jobs if j["match_score"] >= min_score]
    return jobs
