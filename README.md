# Adaptive AI Employee Success Platform

**AetherSuccess** — an autonomous multi-agent employee onboarding & success platform.

Primary application code: [`crew ai/`](./crew%20ai/)  
Full docs: **[crew ai/README.md](./crew%20ai/README.md)**

---

## Why this project

### Problem
Traditional employee onboarding is static, one-size-fits-all, and hard to scale. New hires get the same quizzes and documents regardless of role, progress, or weak topics — while HR lacks clear visibility into who is struggling and why.

### Solution
An autonomous multi-agent system that plans onboarding, retrieves company knowledge with RAG, generates adaptive quizzes, evaluates AI output quality, and mentors each employee using persistent digital memory — all with manager insights and execution traces.

### Impact
Faster, personalized onboarding; fewer knowledge gaps; clear risk signals for managers; and a portfolio-ready demo of production-style agentic AI (planner, tools, RAG, memory, evaluator, observability).

---

## Highlights

- RAG knowledge base (ChromaDB) with PDF upload
- Adaptive AI Mentor with persistent digital memory
- Planner / Orchestrator + Evaluator quality gates
- Tool calling, observability traces, manager insights dashboard
- FastAPI + Docker compatible

---

## Quick start (fresh clone)

```bash
git clone https://github.com/sidra86/AI-Employee-Success-Platform-An-Autonomous-Multi-Agent-Onboarding-System.git
cd AI-Employee-Success-Platform-An-Autonomous-Multi-Agent-Onboarding-System
cd "crew ai"

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux

# Optional: add your OPENAI_API_KEY in .env (works in mock mode without it)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open the app in your browser:

- `/` — Home
- `/dashboard` — Dashboard
- `/knowledge` — Knowledge Base
- `/insights` — Manager Insights
- `/health` — Health check

> **Note:** `.env` is gitignored. Always copy from `.env.example` after cloning.
