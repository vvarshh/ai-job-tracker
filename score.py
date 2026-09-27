#!/usr/bin/env python3
"""Score GTM roles against a profile, with a reason attached to every score.

    python3 score.py                 # 30 most recent
    python3 score.py --limit 100
    python3 score.py --min-score 7   # only write the ones worth opening

Reads the Signal Scraper's output rather than this project's own fetchers.
Those fetchers return almost nothing usable -- MyCareersFuture and SerpAPI both
come back empty, and Remotive returns a couple of dozen unfiltered remote jobs
where the top hit is an office assistant. The scraper already produces 1,000+
GTM-shaped roles in the right markets, so this scores those.

Scoring is batched. One model call per batch of jobs, not one per job: at ~40s
a call, per-job scoring would take half an hour for a single page of results.

The model is reached through account-brief's provider adapter, so this runs on
whatever that is configured with -- including the Claude subscription, with no
API key.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = os.path.dirname(HERE)

# The LLM adapter lives with the research agents; one auth path for everything.
sys.path.insert(0, os.path.join(PROJECTS, "account-brief"))

SCRAPER_CSV = os.path.join(PROJECTS, "others", "startupmap_scraper", "gtm-roles.csv")
OUT_CSV = os.path.join(HERE, "scored-roles.csv")
BATCH_SIZE = 25

PROFILE = """\
Business Analytics (Hons) from NUS School of Computing, specialising in
marketing analytics. Moving into GTM engineering.

- Builds AI agents and data pipelines: Python, SQL, RAG, LangGraph, API
  integration, workflow automation.
- Client-facing delivery: ran discovery with 10+ stakeholders, wrote 30+ user
  stories, owned an integration through launch and two further phases.
- Shipped two production RAG assistants 0->1 in ten weeks and defined the
  success metrics for them.
- Marketing analytics: segmentation, attribution, A/B testing, statistical
  significance.
- Also a content creator with UGC experience, so copy and messaging are real
  skills, not adjacent ones.

Wants: GTM engineer, growth engineer, or forward-deployed/solutions engineering
at an early-stage startup. Not pure SDR/AE quota-carrying roles. Not pure
backend engineering with no customer contact.

Can work in: UK, Singapore, US, or remote.
"""

SYSTEM = """You score job listings against one candidate profile.

Return ONLY a JSON array, one object per job, in the same order you were given
them. No markdown, no prose around it.

[{"score": <1-10>, "reason": "<one sentence, max 20 words>"}, ...]

Scoring:
  9-10  GTM/growth engineering at an early-stage company; the profile's
        engineering AND marketing halves are both used.
  7-8   Strong: forward-deployed, solutions engineering, RevOps with real
        building, or growth where the analytics matter.
  5-6   Partial: adjacent function, or right function at the wrong seniority.
  3-4   Weak: quota-carrying sales, or engineering with no customer contact.
  1-2   Wrong field entirely.

The reason must say WHY, concretely, referencing something in the listing.
Never write "good match" or "strong fit" on their own."""


def load_jobs(limit: int) -> List[Dict[str, Any]]:
    if not os.path.isfile(SCRAPER_CSV):
        sys.exit(
            "No scraper output at {}\n"
            "Run the Signal Scraper first:\n"
            "  cd '{}' && python3 scraper.py".format(
                SCRAPER_CSV, os.path.dirname(SCRAPER_CSV)))
    with open(SCRAPER_CSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    # Already sorted newest-first by the scraper.
    return rows[:limit]


def score_batch(jobs: List[Dict[str, Any]], client) -> List[Dict[str, Any]]:
    listing = "\n".join(
        "{}. {} at {} | {} | {} | stage: {} | {}".format(
            i + 1,
            j.get("Role", ""), j.get("Company", ""),
            j.get("Tier", ""), j.get("Location", ""),
            j.get("Stage", "") or "unknown",
            (j.get("Why Interesting", "") or "")[:140],
        )
        for i, j in enumerate(jobs)
    )
    ask = "CANDIDATE PROFILE:\n{}\n\nJOBS ({}):\n{}".format(PROFILE, len(jobs), listing)
    raw = client.complete(SYSTEM, ask, max_tokens=2000).strip()

    match = re.search(r"\[.*\]", raw, re.S)
    if not match:
        return [{"score": 0, "reason": "model returned no JSON"}] * len(jobs)
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return [{"score": 0, "reason": "malformed JSON from model"}] * len(jobs)

    # A short or long array would silently misalign scores with jobs, so pad
    # and truncate to the batch rather than trusting the count.
    out = []
    for i in range(len(jobs)):
        item = parsed[i] if i < len(parsed) and isinstance(parsed[i], dict) else {}
        out.append({
            "score": int(item.get("score", 0) or 0),
            "reason": str(item.get("reason", "") or ""),
        })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=30, help="how many to score")
    ap.add_argument("--min-score", type=int, default=0, help="only write >= this")
    args = ap.parse_args()

    from brief.llm import LLM, NoProviderConfigured
    try:
        client = LLM()
    except NoProviderConfigured as e:
        sys.exit(str(e))

    jobs = load_jobs(args.limit)
    print("Scoring {} roles with {}\n".format(len(jobs), client))

    scored = []
    for start in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[start:start + BATCH_SIZE]
        print("  batch {}-{}...".format(start + 1, start + len(batch)), flush=True)
        for job, verdict in zip(batch, score_batch(batch, client)):
            job = dict(job)
            job["Score"] = verdict["score"]
            job["Why"] = verdict["reason"]
            scored.append(job)

    scored.sort(key=lambda r: r["Score"], reverse=True)
    keep = [r for r in scored if r["Score"] >= args.min_score]

    if keep:
        cols = ["Score", "Why", "Role", "Company", "Tier", "Location",
                "Stage", "Posted", "Apply URL"]
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(keep)

    print("\n  top matches:")
    for r in keep[:10]:
        print("   {:>2}  {:<38} {:<20} {}".format(
            r["Score"], r["Role"][:38], r["Company"][:20], r["Why"][:70]))
    print("\n  {} scored, {} written to {}".format(
        len(scored), len(keep), os.path.basename(OUT_CSV)))


if __name__ == "__main__":
    main()
