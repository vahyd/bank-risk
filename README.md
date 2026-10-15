# Corporate Banking AI Platform (Open Source)

A modular, self-hosted **AI platform for corporate banking** built entirely with
open-source software. Six integrated AI applications run on a shared corporate
data infrastructure with explainability, dashboards, RBAC and audit trails.

| App | What it does | Models & tools |
|-----|--------------|----------------|
| **1. Credit Risk** | Corporate default probability, LGD/EAD/EL, grades, early warning | XGBoost + logistic baseline, calibration, feature importances |
| **2. Fraud Detection** | Transaction risk scoring, anomaly & chain detection | PyOD Isolation Forest + rules + NetworkX |
| **3. AML** | Suspicious activity, circular flows, case management | Rules + NetworkX + Isolation Forest prioritization |
| **4. Liquidity Forecast** | Cash-flow & balance forecasts, shortage alerts, scenarios | statsmodels ETS + scenario engine |
| **5. RM Decision Support** | Client 360°, meeting briefs, RAG assistant | TF-IDF retrieval + Ollama (Llama 3.1 / Mistral) |
| **6. Client Segmentation** | Behavioral segments and profiles | K-means + HDBSCAN |

Everything runs on **synthetic data** (deterministic, seeded) — no real customer
data. The platform never auto-approves credit or auto-blocks payments.

## Quick start (local, no Docker)

Requires Python 3.12+ and Node 20+.

```bash
# 1. Backend (FastAPI + SQLite default)
cd backend
python3.12 -m venv .venv
./.venv/bin/pip install -r requirements.txt
cp .env.example .env            # optional
./.venv/bin/uvicorn app.main:app --reload --port 8000
# → API on http://localhost:8000 · docs at /docs

# 2. Frontend (React + TypeScript, Vite) — separate terminal
cd frontend
npm install
npm run dev
# → UI on http://localhost:5173
```

First startup generates the synthetic dataset (~120 corporates, 260 accounts,
28k transactions, 110 facilities), trains all six application models, and creates
fraud/AML alerts. This takes ~30–90 s once; artifacts are cached in `data/`.

### Optional: open-source LLM via Ollama

```bash
ollama serve            # or use the docker-compose ollama service
ollama pull llama3.1    # or mistral
```

The RM assistant uses Ollama when reachable and falls back to deterministic
extractive answers otherwise, so the demo always works.

## Docker Compose (PostgreSQL + Ollama)

```bash
docker compose up --build
docker compose exec ollama ollama pull llama3.1   # first time only
```

Services: PostgreSQL 16 (`:5432`), FastAPI (`:8000`), React dev server (`:5173`),
Ollama (`:11434`).

## Repository layout

```
backend/          FastAPI app
  app/
    data/         synthetic generator + ingestion/validation/entity resolution
    ml/           credit, fraud, AML, liquidity, segmentation, RAG, Ollama client
    services/     application service layer
    api/          REST routes (RBAC-protected)
  scripts/        evaluate_models.py → data/evaluation_report.json
  tests/          pytest smoke suite
frontend/         React + TypeScript (Vite) — 10 pages
docs/             architecture, API reference, agent instructions
data/             generated artifacts: raw/cleaned CSVs + model files (gitignored)
backend/data/     SQLite DB for local dev (gitignored)
docker-compose.yml
```

## Tests & evaluation

```bash
cd backend
./.venv/bin/pytest -q                # API smoke tests (seed + train once)
./.venv/bin/python scripts/evaluate_models.py
```

## Documentation

- [docs/architecture.md](docs/architecture.md) — components, data lineage, governance
- [docs/api.md](docs/api.md) — endpoint reference with examples
- [docs/AGENT_INSTRUCTIONS.md](docs/AGENT_INSTRUCTIONS.md) — full spec for AI agents

## Notes

- Synthetic data is for prototyping/demos only.
- XGBoost falls back to scikit-learn HistGradientBoosting when the native OpenMP
  runtime is unavailable (e.g., some macOS setups). On Linux/Docker, XGBoost is used.
- The prototype RBAC uses `X-Role` headers; replace with OIDC/SAML in production.

MIT
