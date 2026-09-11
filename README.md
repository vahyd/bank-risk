# BankRisk — AI Banking Operating System

An AI-powered operating system for commercial banks that assists bankers throughout the entire lending lifecycle — from prospecting to enterprise risk management. **For internal bank use only.**

This is a self-contained front-end demo (HTML/CSS/JS, no dependencies) plus an optional Node.js backend that connects to OpenAI for live AI agent analysis. Open `index.html` directly to run with simulated (local) agent responses, or start the backend for real LLM-driven analysis.

## Run it

**Frontend only (mock AI agent):** just open `index.html` in a browser, or:

```bash
python3 -m http.server 8080
```

Then visit `http://localhost:8080`.

**With live AI agent backend:**

```bash
npm install
cp .env.example .env    # add your OPENAI_API_KEY
npm start               # serves the API on http://localhost:3000
```

Open `index.html` (or serve it) alongside. The frontend auto-detects the backend; without a key the backend returns realistic mock agent responses, so the demo always works.

---

## AI agent features

Every module now has an **agent workflow layer** that visualises how the AI reaches an answer:

- **Step-by-step thinking** — reasoning steps animate in sequence (`.agent-steps`).
- **Tool-use visualization** — the agent "calls" tools including **Automated Spreading** (`extract_financials`) and **Continuous Credit Monitoring** (`monitor_credit`), shown as code-style tool calls with running → complete status.
- **Multi-agent handoff** — the chain of agents involved renders as a handoff pipeline.
- **Confidence & audit trail** — confidence score bar plus a list of cited evidence and recommended actions.
- **Orchestrator router** — every run shows the routing decision (e.g. "Orchestrator → Analyst Partner") based on intent keywords.
- **Dual Workforce (human-in-the-loop)** — on elevated risk, declines, capital breaches, or high-severity AML, a **checkpoint** appears where a human banker must **Approve / Reject**; the decision is stamped into the run.
- **Ask AI on any page** — each module has a *Run AI analysis* widget with suggested questions.
- **Chat panel** — the **Ask the agent team** chat (bottom-right) answers natural-language banking questions with the same workflow trace and routing.

### Digital Partners page

A dedicated **Digital Partners** module (nCino-inspired) shows the agentic operating system:

- **Architecture** — User → Orchestrator → five specialist agents → Dual Workforce checkpoint → shared tools/memory.
- **Five partner roles** — Executive, Analyst, Service, Processor, Client — each with its own system-prompt persona and responsibilities.
- **Engage a partner** — pick a partner (or **Auto route**) to force routing; the chat opens prefilled so you can converse with that specific role.
- **Shared tools** — Automated Spreading (`extract_financials`), Continuous Credit Monitoring (`monitor_credit`), `run_credit_model`, `scan_aml_alerts`, `get_stress_test_result`, `fetch_treasury_forecast`.

### Zenodo Dataset page

The **Dataset** tab is a live version of the Zenodo inspector: it fetches metadata for Zenodo record **18115815** (synthetic firm-level credit-risk dataset, ~20,000 firms) **without downloading the dataset**.

- The backend (`server.js`, `/api/zenodo/:id` and `/api/zenodo/:id/sample`) proxies the Zenodo REST API with a proper `User-Agent`.
- Metadata shown: title, DOI, publication date, license, access, creators, view/download stats, description, file manifest.
- **Feature profile**: exact firm count (**20,000 firms**) and feature count (**13 features**) are computed server-side by parsing the full source file once (cached in memory) — the agent can answer "how many firms / how many features" with the exact numbers.
- Sample preview: the first 30 rows are pulled using an **HTTP Range** request (~64 KB — no full download), parsed, and European decimal commas (`"7229,321243"`) are normalized.
- Backend must be running (`npm start`) since the app proxies Zenodo.

The `server.js` backend uses a single "agent team" system prompt (five Digital Partners + specialist modules, intent router, Dual Workforce flags) and returns structured JSON (summary, steps, tools, agents, confidence, evidence, recommendations, routedTo, humanApprovalNeeded). When no `OPENAI_API_KEY` is set, a deterministic local engine generates the same structure from the app's own data, so the UI behaves identically either way.

---

## Modules

| Module                        | User                    | Drives                  |
|-------------------------------|-------------------------|-------------------------|
| Relationship Manager Copilot  | Corporate Bankers       | Grow revenue            |
| SME Credit Underwriting Agent | Credit Officers         | Improve lending quality |
| Early Warning System          | Risk Team               | Reduce defaults         |
| Treasury & Liquidity Copilot  | Treasury Department     | Manage liquidity        |
| Portfolio Risk Simulator      | CRO / Senior Management | Manage enterprise risk  |
| Stress Testing                | Risk Team / CRO         | Regulatory capital      |
| CFO AI Recommendations        | CFO / Senior Management | Capital & risk advice   |
| AML Investigation Agent       | Compliance Team         | Reduce compliance risk  |
| Digital Partners              | All users               | Agentic orchestration   |

---

## Core platform vision

```
Prospect → Relationship Manager → Credit Underwriting → Loan Approval
         → Portfolio Monitoring → Treasury Management → Enterprise Risk Management
```

---

## Module highlights

- **RM Copilot** — Customer 360 view (deposits, loans, profitability), meeting-brief generator, cross-sell engine, risk notifications.
- **Credit Underwriting Agent** — credit score, probability of default, financial analysis, auto-generated credit memo, approval recommendation.
- **Early Warning System** — client risk score, probability of distress, and deterioration drivers (revenue decline, overdraft usage, falling deposits).
- **Treasury Copilot** — liquidity forecasting, funding-gap projection, and funding recommendations.
- **Portfolio Risk Simulator** — stress scenarios (recession, housing crash, rate hike, currency crisis, CRE downturn) with credit-loss and capital-ratio impact.
- **AML Agent** — suspicious-activity detection, transaction-network analysis, customer risk scoring, investigation reports.

---

## Tech

Frontend: plain HTML/CSS/JS. `index.html` is the shell, `styles.css` the theme, `app.js` the data and rendering logic plus the agent layer. No frontend build step or dependencies.

Backend: Node.js + Express (`server.js`) with the OpenAI SDK for the agent analysis endpoint. Env config via `.env` (see `.env.example`).

MIT
