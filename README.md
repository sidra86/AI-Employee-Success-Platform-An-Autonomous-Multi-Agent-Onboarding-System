# Adaptive AI Employee Success Platform

This repository contains **AetherSuccess** — an autonomous multi-agent employee success platform.

Primary application code lives in [`crew ai/`](./crew%20ai/).

See the full documentation:

👉 **[crew ai/README.md](./crew%20ai/README.md)**

### Highlights

- RAG knowledge base (ChromaDB) with PDF upload
- Adaptive AI Mentor with persistent digital memory
- Planner / Orchestrator + Evaluator quality gates
- Tool calling, observability traces, manager insights dashboard
- FastAPI + Docker compatible

### Run

```bash
cd "crew ai"
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy env_example.txt .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8025
```

Open `http://127.0.0.1:8025`
