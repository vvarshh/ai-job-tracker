"""
agent/pipeline.py — LangGraph pipeline: fetch → score → rank.

Nodes:
  1. fetch_jobs  — pulls from all sources and merges
  2. score_jobs  — LLM scores each job 1-10 against user profile
  3. rank_jobs   — sorts by score descending

Usage:
    from agent.pipeline import run_pipeline
    results = run_pipeline(profile="...", min_score=6)
"""

import json
import os
from typing import Any, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from agent.prompts import SCORE_PROMPT
from fetchers import remotive, mycareersfuture, serpapi


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class PipelineState(TypedDict):
    profile: str
    raw_jobs: list[dict[str, Any]]
    scored_jobs: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def fetch_jobs(state: PipelineState) -> PipelineState:
    """Pull jobs from all sources and merge into a single list."""
    jobs: list[dict] = []
    jobs.extend(mycareersfuture.fetch_jobs())  # free, no key, SG gov portal
    jobs.extend(serpapi.fetch_jobs())           # Google Jobs (LinkedIn, Indeed, etc.)
    jobs.extend(remotive.fetch_jobs())          # remote AI/ML roles
    return {**state, "raw_jobs": jobs}


def score_jobs(state: PipelineState) -> PipelineState:
    """Score each job against the user profile using Claude."""
    llm = ChatAnthropic(
        model="claude-3-haiku-20240307",  # fast + cheap for batch scoring
        api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        max_tokens=100,
    )

    profile = state["profile"]
    scored = []

    for job in state["raw_jobs"]:
        prompt = SCORE_PROMPT.format(
            profile=profile,
            title=job["title"],
            company=job["company"],
            location=job["location"],
            salary=job["salary"],
            description=job["description"][:500],
        )
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            data = json.loads(response.content.strip())
            job["match_score"] = int(data.get("score", 0))
            job["match_reason"] = data.get("reason", "")
        except Exception:
            job["match_score"] = 0
            job["match_reason"] = "Could not score this role."
        scored.append(job)

    return {**state, "scored_jobs": scored}


def rank_jobs(state: PipelineState) -> PipelineState:
    """Sort jobs by match score descending."""
    ranked = sorted(state["scored_jobs"], key=lambda j: j["match_score"], reverse=True)
    return {**state, "scored_jobs": ranked}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def _build_graph() -> Any:
    g = StateGraph(PipelineState)
    g.add_node("fetch_jobs", fetch_jobs)
    g.add_node("score_jobs", score_jobs)
    g.add_node("rank_jobs", rank_jobs)
    g.set_entry_point("fetch_jobs")
    g.add_edge("fetch_jobs", "score_jobs")
    g.add_edge("score_jobs", "rank_jobs")
    g.add_edge("rank_jobs", END)
    return g.compile()


_graph = _build_graph()


def run_pipeline(profile: str, min_score: int = 0) -> list[dict[str, Any]]:
    """Run the full fetch → score → rank pipeline and return filtered results."""
    result = _graph.invoke({"profile": profile, "raw_jobs": [], "scored_jobs": []})
    jobs = result["scored_jobs"]
    if min_score > 0:
        jobs = [j for j in jobs if j["match_score"] >= min_score]
    return jobs
