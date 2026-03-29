# 🤖 AI Job Tracker — Singapore

A deployable AI-powered job board tracker that fetches live AI/ML roles in Singapore, scores them against your skills profile using a LangGraph agent + Claude, and surfaces ranked matches in a Streamlit dashboard.

**Live demo**: *(add your Streamlit Cloud URL here after deploying)*

---

## What it does

1. **Fetches** live AI Engineer / AI PM / AI Agents roles from Remotive and Adzuna
2. **Scores** each job 1–10 against your skills profile using a LangGraph agent (Claude as the LLM)
3. **Ranks** the best matches and displays them with colour-coded scores, salary, location, and a one-line match reason
4. **Filters** by minimum score and job source

---

## Architecture

```
ai-job-tracker/
├── app.py                  # Streamlit UI
├── agent/
│   ├── pipeline.py         # LangGraph: fetch → score → rank
│   └── prompts.py          # Claude scoring prompt
├── fetchers/
│   ├── adzuna.py           # Adzuna API (Singapore, free tier)
│   └── remotive.py         # Remotive API (remote roles, no key needed)
├── profile.py              # Default candidate profile
├── requirements.txt
└── .env.example
```

---

## Tech stack

- [LangGraph](https://github.com/langchain-ai/langgraph) — multi-step agent pipeline
- [LangChain Anthropic](https://python.langchain.com/docs/integrations/chat/anthropic/) — Claude as scoring LLM
- [Streamlit](https://streamlit.io) — web UI
- [Adzuna API](https://developer.adzuna.com) — Singapore job listings (free tier)
- [Remotive API](https://remotive.com/api/remote-jobs) — remote AI/ML roles (no key needed)

---

## Setup

### 1. Clone & install

```bash
git clone https://github.com/vvarshh/ai-job-tracker
cd ai-job-tracker
pip install -r requirements.txt
```

### 2. Add API keys

```bash
cp .env.example .env
```

Edit `.env`:
```
ANTHROPIC_API_KEY=your_key       # console.anthropic.com
ADZUNA_APP_ID=your_id            # developer.adzuna.com (free)
ADZUNA_APP_KEY=your_key
```

> Remotive works with no API key. Adzuna is optional but recommended.

### 3. Run

```bash
streamlit run app.py
```

---

## Deploy to Streamlit Cloud (free)

1. Push repo to GitHub (public)
2. Go to [share.streamlit.io](https://share.streamlit.io) → connect repo
3. Set entry point: `app.py`
4. Add your API keys under **Settings → Secrets**:
```toml
ANTHROPIC_API_KEY = "xxx"
ADZUNA_APP_ID = "xxx"
ADZUNA_APP_KEY = "xxx"
```
5. Deploy — auto-updates on every push

---

## Customising the profile

Edit `profile.py` to change the default candidate profile, or edit it directly in the Streamlit sidebar at runtime. The LangGraph agent re-scores all jobs against the updated profile on next refresh.
