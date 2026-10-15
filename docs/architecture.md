# Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    React + TypeScript (Vite)                    │
│   Overview · Customers · Credit · Fraud · AML · Liquidity · RM ·│
│              Segmentation · Models · Admin                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST /api  (X-Role RBAC header)
┌──────────────────────────────▼──────────────────────────────────┐
│                       FastAPI (Python 3.12)                     │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────────────┐  │
│  │ credit    │ │ fraud     │ │ aml       │ │ liquidity      │  │
│  │ XGBoost + │ │ PyOD IF + │ │ rules +   │ │ ETS + scenarios│  │
│  │ logistic  │ │ rules +   │ │ NetworkX  │ │                │  │
│  │ baseline  │ │ NetworkX  │ │ + IF      │ │                │  │
│  └───────────┘ └───────────┘ └───────────┘ └────────────────┘  │
│  ┌───────────┐ ┌───────────┐ ┌───────────────────────────────┐  │
│  │ RM RAG    │ │ segment.  │ │ governance: RBAC · audit ·    │  │
│  │ TF-IDF +  │ │ KMeans +  │ │ ModelRun registry · quality   │  │
│  │ Ollama    │ │ HDBSCAN   │ └───────────────────────────────┘  │
│  └───────────┘ └───────────┘                                    │
└──────────────┬───────────────────────────────────────────────────┘
               │ SQLAlchemy 2.0
┌──────────────▼───────────────────────────────────────────────────┐
│   PostgreSQL (production / Docker)  ·  SQLite (local dev)        │
│   customers · accounts · transactions · facilities · repayments  │
│   alerts · investigation_cases · forecasts · segments ·          │
│   model_runs · audit_logs · users                                │
└──────────────────────────────────────────────────────────────────┘
               ▲
               │ synthetic generator (deterministic, seeded)
        data/raw → data/cleaned → features → predictions → decisions
```

## Data lineage

| Layer | Location | Contents |
|-------|----------|----------|
| Raw | `data/raw/*.csv` | Generated synthetic frames as-is |
| Cleaned | `data/cleaned/*.csv` | Validated, deduplicated, entity-resolved |
| Features | computed in `app/ml/features.py` | Model-ready feature matrices |
| Predictions | `data/models/*.joblib` + `model_runs` table | Trained artifacts + metrics |
| Decisions | `alerts`, `investigation_cases`, `audit_logs` | Human-reviewed outcomes |

## Model registry

Every training run writes a `model_runs` row with name, version, metrics, params,
and status — an MLflow-compatible schema. Retrain via `POST /api/admin/train` or
`scripts/evaluate_models.py`.

## RBAC

Roles: `admin`, `analyst`, `rm`, `compliance`, `treasury`. The prototype accepts
`X-User` / `X-Role` headers (UI has a role switcher); when no `X-Role` header is
sent it defaults to `admin`. Production should replace this with OIDC/SAML and
short-lived tokens.

| Role | Permissions |
|------|-------------|
| `admin` | `*` (everything) |
| `analyst` | `dashboard:read`, `customers:read`, `credit:read`, `fraud:read`, `fraud:write`, `aml:read`, `liquidity:read`, `segmentation:read`, `models:read` |
| `rm` | `dashboard:read`, `customers:read`, `credit:read`, `liquidity:read`, `segmentation:read`, `rm:read`, `rm:write` |
| `compliance` | `dashboard:read`, `customers:read`, `aml:read`, `aml:write`, `audit:read` |
| `treasury` | `dashboard:read`, `customers:read`, `liquidity:read`, `liquidity:write` |

## Open-source LLM

`app/ml/llm.py` calls Ollama's `/api/generate` and `/api/chat` (default model
`llama3.1`, configurable to `mistral`). When Ollama is unreachable the platform
answers from retrieved records deterministically, so demos always work.
