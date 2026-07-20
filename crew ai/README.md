# Adaptive AI Employee Success Platform (AetherSuccess)

Autonomous, multi-agent employee success platform built with **FastAPI**, **CrewAI-compatible agents**, **RAG (ChromaDB)**, **persistent digital memory**, and **full observability**.

Formerly the CrewAI Employee Onboarding System — now upgraded into a production-style agentic platform that continuously learns from every interaction.

---

## Why this project

### Problem
Employee onboarding is often manual, generic, and poorly tracked. Companies struggle to personalize learning, surface knowledge gaps early, and prove that new hires actually understand policies and role expectations.

### Solution
AetherSuccess orchestrates specialized AI agents (Planner → RAG → Quiz → Video → Progress → Feedback → Evaluator → Mentor → Memory) with tool calling, document retrieval, and persistent learning profiles so every employee gets an adaptive mentor — not a fixed checklist.

### Impact
- Personalized onboarding paths based on weak/strong topics
- Grounded answers from uploaded handbooks and policies (RAG)
- Quality-gated AI outputs before employees see them
- Manager visibility into risk, gaps, completion, and agent activity

---

## What makes this different

| Capability | Description |
|---|---|
| **RAG Knowledge Base** | Admins upload handbooks, policies, SOPs, PDFs → chunked, embedded, retrieved by agents |
| **Adaptive AI Mentor** | Persistent per-employee learning profile (weak/strong topics, confidence, style, roadmap) |
| **Planner / Orchestrator** | Decides which specialized agent runs next |
| **Tool calling** | Employee lookup, knowledge search, policies, reports, mock email |
| **Evaluator Agent** | Quality-gates quizzes & feedback; auto-regenerates when quality is low |
| **Observability** | Traces: agents, tools, timing, token estimates, errors, workflow tree |

---

## Architecture

```text
┌──────────────────────────────────────────────────────────────────────┐
│                     FastAPI Web + Manager UI                         │
│   Dashboard · Insights · Knowledge Upload · Employee Mentor Profile  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────────┐
│              OnboardingCrew (Autonomous Orchestrator)                │
│                                                                      │
│  Planner → RAG → Quiz → Video → Progress → Feedback                  │
│       → Evaluator → Mentor → Memory → Notify                         │
└───┬──────────┬──────────┬──────────┬──────────┬──────────┬───────────┘
    │          │          │          │          │          │
 agents/    tools/      rag/     memory/   evaluator/  observability/
 planner/            vector_store/
```

### Suggested module layout

```text
agents/           # Quiz, Video, Progress, Feedback, Mentor, Planner, Evaluator
tools/            # Tool-calling layer
rag/              # Ingest + retrieve pipeline
vector_store/     # ChromaDB (with in-memory fallback)
memory/           # Digital memory + Adaptive Mentor
planner/          # Execution plan generation
evaluator/        # Quality gates + regeneration
observability/    # Traces, spans, token estimates
app/              # FastAPI routes + orchestrator
database/         # SQLAlchemy models
templates/        # UI
```

---

## Agent workflow

```text
Employee joins
     │
     ▼
Planner Agent  ──► ordered plan (memory-aware)
     │
     ▼
RAG Retriever  ──► handbook / policy context (tools: document_retrieval, policy_access)
     │
     ▼
Quiz Agent     ──► grounded quizzes (difficulty adapted from memory)
     │
     ▼
Video Agent    ──► engagement / comprehension analysis
     │
     ▼
Progress Agent ──► metrics + report_generation tool
     │
     ▼
Feedback Agent ──► personalized coaching
     │
     ▼
Evaluator      ──► quality score; regenerate if low
     │
     ▼
Mentor Agent   ──► roadmap, risk, next modules
     │
     ▼
Memory Service ──► persist learning profile
     │
     ▼
Notifier       ──► mock_email to employee
```

---

## RAG pipeline

1. **Upload** PDF/TXT via `/knowledge` or `POST /api/knowledge/upload`
2. **Extract** text (`pypdf`)
3. **Chunk** overlapping windows (`rag/chunker.py`)
4. **Embed** with local deterministic embeddings (works offline) and store in **ChromaDB** (`vector_store/`)
5. **Retrieve** top-k snippets for agent prompts via tools

Fallback: if ChromaDB is unavailable, an in-memory cosine store is used so the app still runs.

---

## Digital memory & Adaptive AI Mentor

Each employee has an `EmployeeLearningProfile` that persists:

- quiz history, weak/strong topics
- learning speed, completed modules
- previous feedback, common mistakes
- engagement & confidence scores
- preferred learning style
- risk level + personalized roadmap

**Mentor behavior**

- Skip topics already mastered
- Add remedial quizzes for weak areas
- Adapt difficulty from confidence
- Predict employees who may struggle
- Recommend next modules + learning modality

---

## Tool calling

| Tool | Purpose |
|---|---|
| `employee_lookup` | Search employees by id/email/name |
| `progress_retrieval` | Quizzes, reports, memory snapshot |
| `document_retrieval` | RAG context snippets |
| `knowledge_search` | Semantic search JSON results |
| `policy_access` | Prefer policy/HR categories |
| `report_generation` | Structured manager report |
| `mock_email` | Notification outbox (no real SMTP) |

---

## Observability

Every autonomous run produces a trace with:

- agent execution order
- tool usage
- duration (ms)
- estimated token usage
- errors / events
- nested span tree

Persisted in `agent_execution_logs` and shown on **Manager Insights**.

---

## Design decisions

1. **CrewAI optional** — `mock_crew.py` keeps the system runnable without heavy LLM deps; real CrewAI/OpenAI plug in when installed.
2. **Local embeddings by default** — deterministic hash embeddings avoid mandatory GPU/model downloads; swap for OpenAI/sentence-transformers later.
3. **Planner outside the LLM loop** — deterministic, auditable plans with memory-aware branching.
4. **Evaluator as a gate** — prevents low-quality quizzes/feedback from reaching employees.
5. **SQLite + Chroma files** — simple Docker volume story for demos; swap DB URL for Postgres in production.

---

## Quick start (local)

```bash
cd "crew ai"
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
# source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env          # Windows
# cp .env.example .env          # macOS / Linux
# Optional: set OPENAI_API_KEY in .env

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Useful routes after startup:

- `/` — Home
- `/dashboard` — Dashboard
- `/knowledge` — Knowledge Base
- `/insights` — Manager Insights
- `/health` — Health check

---

## Docker

```bash
cp .env.example .env
# set OPENAI_API_KEY if desired
docker-compose up --build
```

The app runs on port **8000**. Volumes persist `./data` (SQLite, Chroma, uploads).

---

## Key API endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/employees/` | Create employee (+ seed memory) |
| POST | `/employees/{id}/start-onboarding` | Run full autonomous workflow |
| POST | `/api/knowledge/upload` | Index PDF/TXT |
| POST | `/api/knowledge/search` | RAG search |
| GET | `/api/employees/{id}/memory` | Digital memory JSON |
| GET | `/api/insights` | Manager insights |
| GET | `/api/traces` | Observability traces |
| GET | `/api/tools` | Registered tools |
| GET | `/health` | Health + RAG stats |

---

## Limitations

- Mock LLM mode generates demo quizzes/feedback (not company-specific) unless OpenAI/CrewAI is configured.
- Local hash embeddings are good for demos; production should use stronger embedding models.
- Mock email does not send real messages.
- Single-node SQLite/Chroma is not multi-region HA.
- AuthN/AuthZ is not implemented (add for production).

---

## Future improvements

- OpenAI / Voyage / HuggingFace embeddings
- Real SMTP + Slack notifications
- SSO / RBAC for HR admins vs managers
- Postgres + managed vector DB
- Streaming agent UI / websocket traces
- A/B testing of mentor strategies
- Multi-language onboarding content
- Integration with HRIS (Workday, BambooHR)

---

## Brand

**Product:** Adaptive AI Employee Success Platform  
**Short name:** AetherSuccess  
**Tagline:** Autonomous agents. Persistent memory. Personal mentoring.

---

Built for production-style agentic onboarding — modular, Docker-ready, and extensible.
