# Corporate Banking Decision Intelligence

An AI-powered **Corporate Banking Decision Intelligence** platform — a multi-agent system that replicates **Moody's Banking Decision Intelligence** capabilities. A **Chief Risk Officer Agent** orchestrates **14 specialist agents** spanning the full commercial-lending lifecycle: underwriting, credit assessment, portfolio monitoring, early warning, concentration risk, covenant monitoring, IFRS 9 / CECL provisioning, capital allocation, loan pricing, stress testing, and loan-committee support.

**For internal bank use only.** The platform assists human bankers and risk officers and **never makes final credit decisions** — every recommendation is explainable, auditable, and traceable.

---

## Agent architecture

```text
Chief Risk Officer Agent (orchestrator)
│
├── Credit Underwriting Agent
├── Financial Analysis Agent
├── Portfolio Risk Agent
├── Early Warning Agent
├── Covenant Monitoring Agent
├── Industry Risk Agent
├── Macroeconomic Agent
├── Concentration Risk Agent
├── IFRS9 / CECL Agent
├── Pricing Agent
├── Capital Allocation Agent
├── Compliance & KYC Agent
├── Stress Testing Agent
└── Credit Memo Agent
```

### The 15 agents

| # | Agent | Purpose | Key outputs |
|---|-------|---------|-------------|
| 1 | **Chief Risk Officer Agent** (orchestrator) | Consolidates outputs, resolves conflicts, prioritizes risks, produces executive summaries, prepares loan-committee packages | Risk Rating, Key Risks, Recommended Actions, Capital Impact, Expected Loss, Portfolio Impact |
| 2 | **Credit Underwriting Agent** | Assesses borrower creditworthiness (PD, LGD, EAD, repayment capacity, leverage, liquidity) | Internal Rating, PD, LGD, Expected Loss, Key Drivers |
| 3 | **Financial Analysis Agent** | Spreading & ratio analysis (profitability, leverage, liquidity, coverage) | Financial Strength Score, Trend Analysis, Peer Benchmarking |
| 4 | **Portfolio Risk Agent** | Monitors portfolio health (sector/geographic exposure, rating migration, NPL, EL trends) | Portfolio Risk Dashboard, Top Exposures, Emerging Risks |
| 5 | **Early Warning Agent** | Detects deterioration before default (news, spreads, covenant breaches, payment delays, rating changes) | Early Warning Level — Red / Amber / Green |
| 6 | **Covenant Monitoring Agent** | Tracks covenant compliance (Debt/EBITDA < 4.0×, DSCR > 1.25×, minimum liquidity) | Compliant / Watchlist / Breach |
| 7 | **Industry Risk Agent** | Assesses industry conditions (growth, competition, regulation, commodity exposure) | Industry Risk Score, Outlook |
| 8 | **Macroeconomic Agent** | Measures economic impact (GDP, inflation, rates, FX, unemployment, real estate) | Base / Upside / Downside Case |
| 9 | **Concentration Risk Agent** | Identifies excessive concentrations (industry, country, region, single-name, corporate group) | Top 10 Borrowers / Industries / Countries |
| 10 | **IFRS9 / CECL Agent** | Calculates impairment (stage classification, 12-month & lifetime ECL, provision movement) | Allowance, Provision Expense, Coverage Ratio |
| 11 | **Pricing Agent** | Recommends risk-adjusted pricing (PD, LGD, capital usage, funding cost, relationship revenue) | Minimum Spread, Target Spread, RAROC |
| 12 | **Capital Allocation Agent** | Optimizes capital usage (economic capital, RWA, capital consumption) | Capital Efficiency Score |
| 13 | **Compliance & KYC Agent** | Perpetual KYC (sanctions, PEP, adverse media, UBO, AML risk) | Screening results, SAR recommendations |
| 14 | **Stress Testing Agent** | Runs scenarios (recession, rate shock, real-estate crash, FX crisis, sector shock) | Impact on PD, losses, capital, liquidity |
| 15 | **Credit Memo Agent** | Generates credit-committee packages | Borrower overview, financials, industry, risk, collateral, stress, recommendation, conditions |

### Global rules (every agent must)

1. Explain reasoning · 2. Cite data sources · 3. Show calculations · 4. Quantify uncertainty · 5. Flag missing data · 6. Maintain audit logs · 7. Escalate material risks · 8. Never override policy limits · 9. Never approve loans automatically · 10. Produce regulator-ready outputs.

### Dual Workforce (human-in-the-loop)

On elevated risk, declines, capital breaches, covenant breaches, or high-severity AML cases, a **checkpoint** appears where a human banker must **Approve / Reject**; the decision is stamped into the run. The platform never auto-approves loans.

---

## Modules (UI pages)

| Module | Agent / role | Purpose |
|--------|-------------|---------|
| Overview | Chief Risk Officer | Executive dashboard, agent ranking, lending lifecycle, platform vision |
| Credit Committee | Chief Risk Officer | Consolidated risk rating, key risks, recommended actions, capital & loss impact |
| Credit Underwriting | Credit Underwriting Agent | Application queue, PD/LGD/EAD, credit score, grade, auto-generated memo |
| Financial Analysis | Financial Analysis Agent | Spreading & ratio dashboard (profitability, leverage, liquidity, coverage) |
| Credit Memo | Credit Memo Agent | Loan-committee package (overview, financials, industry, risk, collateral, stress, conditions) |
| Early Warning | Early Warning Agent | Watchlist, risk/distress scores, deterioration drivers, severity filters |
| Covenant Monitoring | Covenant Monitoring Agent | Covenant tests with Compliant / Watchlist / Breach status |
| Portfolio Risk | Portfolio Risk Agent | Sector/geographic exposure, expected-loss trends, scenario stress |
| Concentration Risk | Concentration Risk Agent | Top borrowers, industries and countries; concentration limits |
| Industry Risk | Industry Risk Agent | Sector growth, competition, regulation, commodity exposure, outlook |
| Macroeconomic | Macroeconomic Agent | Base / upside / downside macro cases |
| Stress Testing | Stress Testing Agent | Scenario + severity stress on capital and liquidity |
| Capital Allocation | Capital Allocation Agent | Economic capital, RWA, RORAC by business line, efficiency score |
| IFRS 9 / CECL | IFRS9 / CECL Agent | Stage classification, 12-month vs lifetime ECL, allowance & coverage |
| Pricing | Pricing Agent | Minimum/target spread and RAROC per deal |
| Compliance & KYC | Compliance & KYC Agent | AML/Sanctions/PEP alert queue, investigation, SAR recommendations |
| Treasury | Macroeconomic Agent | Liquidity forecast, funding-gap projection, funding recommendation |
| RM Copilot | Chief Risk Officer | Customer 360, cross-sell engine, meeting briefs, risk notifications |
| CFO AI | Chief Risk Officer | Executive recommendations across treasury, risk and capital |
| Agent Architecture | Chief Risk Officer | Full 15-agent org chart, global rules, engage-any-agent |
| Dataset | Credit Underwriting | Live Zenodo metadata, feature profile, sample preview, training status |

---

## Dataset training

The system is grounded on **Zenodo record 18115815** — a fully synthetic firm-level credit-risk dataset (~20,000 firms, 13 features: Size, Leverage, Profit_Margin, RD_Intensity, Org_Complexity, Sector, Region, base_hazard, cov_effect, hazard, Event_Time, Status, Firm_ID).

`train/agents.js` fits a **ridge-regression (SGD, L2) model** on the dataset's `hazard` score (80/20 train/test split) and derives per-section knowledge for every agent — grade bands, watchlist, sector/region PD, concentration shares, stress scenarios, AML outliers, and more — persisted to `data/trained/agents.json`.

Every agent answer that touches portfolio, credit, stress, or risk is grounded on these trained numbers. The model is re-fit on demand via `POST /api/train` (or auto-trained on first startup if no artifact exists).

**Note:** the data is synthetic and is for prototyping/demos only — never real customer data.

---

## Run it

```bash
npm install
cp .env.example .env      # optional: add your OPENAI_API_KEY
npm start                 # serves the app + API on http://localhost:3000
```

Open **http://localhost:3000**. With no `OPENAI_API_KEY` set, the backend returns deterministic **mock agent responses** grounded on the trained dataset model, so the demo always works. With a key, the same 15-agent team runs through the OpenAI model (`gpt-4o` by default).

### Backend API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agent/health` | Health + mode (`ai` / `mock`) + trained-model status |
| `POST` | `/api/agent/analyze` | Run the agent team on `{ query, context }` → structured JSON (summary, steps, tools, agents, confidence, evidence, recommendations, routedTo, humanApprovalNeeded) |
| `POST` | `/api/agent/chat` | Multi-turn agent chat on `{ messages }` |
| `GET` | `/api/train/status` | Trained-model metadata and per-section summaries |
| `POST` | `/api/train` | Re-train the agents on the dataset |
| `GET` | `/api/zenodo/:id` | Zenodo record metadata (no full download) |
| `GET` | `/api/zenodo/:id/stats` | Exact firm/feature counts parsed server-side |
| `GET` | `/api/zenodo/:id/sample` | First 30 rows via HTTP Range (no full download) |

### Agent output schema

```json
{
  "summary": "Concise plain-text answer",
  "steps": [{"title": "step label", "detail": "explanation"}],
  "tools": [{"name": "extract_financials", "args": "APP-1042", "status": "complete"}],
  "agents": [{"name": "Credit Underwriting Agent", "role": "scored the application", "status": "complete"}],
  "confidence": 87,
  "evidence": ["cited data point"],
  "recommendations": ["next action"],
  "routedTo": "Credit Underwriting Agent",
  "humanApprovalNeeded": false
}
```

---

## Tech

- **Frontend:** plain HTML/CSS/JS (`index.html`, `styles.css`, `app.js`) — no build step or dependencies. Includes a progressive-reveal agent-workflow renderer (reasoning steps, tool calls, agent handoffs, confidence bar, evidence/audit trail, Dual Workforce checkpoint).
- **Backend:** Node.js + Express (`server.js`) with the OpenAI SDK for live agent analysis. Env config via `.env`.
- **Training:** `train/agents.js` — ridge regression on the Zenodo synthetic dataset; artifacts in `data/trained/agents.json`.

MIT
