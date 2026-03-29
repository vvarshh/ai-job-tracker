"""
agent/prompts.py — LLM prompt templates for job scoring.
"""

BATCH_SCORE_PROMPT = """\
You are a career coach helping an AI Engineer find their best job matches in Singapore.

Score each job listing against the candidate profile. Return a JSON array — one object per job, in the same order.

Rules:
- 9-10: Near-perfect match (AI-native role, exact stack, Singapore-based)
- 7-8: Strong match (AI-focused, most skills align)
- 5-6: Partial match (some AI involvement, transferable skills)
- 1-4: Weak match (minimal AI, wrong domain)

Candidate Profile:
PROFILE_PLACEHOLDER

Jobs to score:
JOBS_PLACEHOLDER

Return ONLY a valid JSON array, no markdown, no explanation:
[{"score": <int>, "reason": "<one sentence>"}, ...]
"""
