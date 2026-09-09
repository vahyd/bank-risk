# BankRisk — AI Banking Operating System

An AI-powered operating system for commercial banks that assists bankers throughout the entire lending lifecycle — from prospecting to enterprise risk management. **For internal bank use only.**

This is a self-contained front-end demo (HTML/CSS/JS, no dependencies). Open `index.html` or serve the folder:

```bash
python3 -m http.server 8080
```

Then visit `http://localhost:8080`.

---

## Modules

| Module                        | User                    | Drives                  |
|-------------------------------|-------------------------|-------------------------|
| Relationship Manager Copilot  | Corporate Bankers       | Grow revenue            |
| SME Credit Underwriting Agent | Credit Officers         | Improve lending quality |
| Early Warning System          | Risk Team               | Reduce defaults         |
| Treasury & Liquidity Copilot  | Treasury Department     | Manage liquidity        |
| Portfolio Risk Simulator      | CRO / Senior Management | Manage enterprise risk  |
| AML Investigation Agent       | Compliance Team         | Reduce compliance risk  |

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

Plain HTML/CSS/JS. `index.html` is the shell, `styles.css` the theme, `app.js` the data and rendering logic. No build step or dependencies.

MIT
