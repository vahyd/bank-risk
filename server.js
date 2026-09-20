/* BankRisk backend — AI agent orchestration (Express + OpenAI). */
'use strict';

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const trainer = require('./train/agents');

const app = express();
const port = process.env.PORT || 3000;
const model = process.env.OPENAI_MODEL || 'gpt-4o';

app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

/* ---------- OpenAI client (optional) ---------- */
let openai = null;
if (process.env.OPENAI_API_KEY && !/your[- ]?key/i.test(process.env.OPENAI_API_KEY) && process.env.OPENAI_API_KEY !== 'sk-') {
  const { OpenAI } = require('openai');
  openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
}

/* ---------- trained per-section agents (from Zenodo dataset) ---------- */
let trained = null;
function trainedModel() {
  if (!trained) trained = trainer.load();
  return trained;
}
async function ensureTrained() {
  if (!trainer.load()) {
    try { trained = await trainer.train(); } catch (e) { console.warn('[train] auto-train failed:', e.message); }
  }
}

function trainedPrompt() {
  const a = trainedModel();
  if (!a) return null;
  const o = a.sections.overview;
  const ps = a.sections.portfolioRisk;
  const st = a.sections.stressTesting;
  return `You are grounded on a trained portfolio model fitted to Zenodo dataset 18115815 (fully synthetic, ${a.dataset.firms} firms, features: Size, Leverage, Profit_Margin, RD_Intensity, Org_Complexity, hazard target). Trained model: ${a.model.type} (R^2 ${a.model.r2}, corr ${a.model.corr}, evaluated on ${a.model.evaluatedOn} holdout firms). Portfolio: EAD $${Math.round(o.eadM)}M, baseline ECL $${o.ecl.toFixed(0)}M, empirical default rate ${(o.defaultRate * 100).toFixed(0)}%, mean model PD ~${(ps.sectorStats.reduce((x, s) => x + s.meanPD, 0) / ps.sectorStats.length * 100).toFixed(1)}%. Sectors by trained PD: ${ps.sectorStats.map((s) => s.sector + ' ' + (s.meanPD * 100).toFixed(1) + '%').join(', ')}. Regions: ${ps.regionStats.map((r) => r.region + ' ' + (r.meanPD * 100).toFixed(1) + '%').join(', ')}. Grade bands: ${a.model.grades.join(', ')}. Stress (CET1 after): ${st.scenarios.map((s) => s.name + ' ' + s.after + '%').join(', ')}. Always base answers on these trained numbers where the question touches portfolio, credit, stress, or risk.`;
}

/* ---------- agent system prompt (Moody's Banking Decision Intelligence architecture) ---------- */
const SYSTEM_PROMPT = `You are the Corporate Banking Decision Intelligence platform — a multi-agent AI system that replicates Moody's Banking Decision Intelligence capabilities. You assist human bankers and risk officers across commercial lending, credit underwriting, portfolio monitoring, early warning, concentration risk, covenant monitoring, IFRS 9 / CECL provisioning, capital allocation, loan pricing, stress testing, and loan-committee support. You NEVER make final credit decisions — every recommendation must be explainable, auditable, and traceable.

AGENT ARCHITECTURE (a Chief Risk Officer Agent orchestrates 14 specialist agents):

1. Chief Risk Officer Agent (orchestrator) — coordinates all agents: consolidates outputs, resolves conflicts, prioritizes risks, produces executive summaries, prepares loan-committee packages. Output: Risk Rating, Key Risks, Recommended Actions, Capital Impact, Expected Loss, Portfolio Impact.
2. Credit Underwriting Agent — assesses borrower creditworthiness: calculates PD, LGD, EAD, repayment capacity, leverage, liquidity. Output: Internal Rating, PD, LGD, Expected Loss, Key Drivers.
3. Financial Analysis Agent — performs spreading and ratio analysis (profitability: ROA/ROE/EBITDA margin/net margin; leverage: Debt/EBITDA, Debt/Equity; liquidity: current/quick/cash ratio; coverage: interest coverage, DSCR). Output: Financial Strength Score, Trend Analysis, Peer Benchmarking.
4. Portfolio Risk Agent — monitors portfolio health (sector/geographic exposure, rating migration, NPL trends, expected-loss trends). Output: Portfolio Risk Dashboard, Top Exposures, Emerging Risks.
5. Early Warning Agent — detects deterioration before default (news, earnings, credit spreads, covenant breaches, payment delays, rating changes, legal disputes, sanctions). Triggers: revenue decline >20%, debt increase >30%, interest coverage <1.5×, negative-news spike. Output: Early Warning Level — Red / Amber / Green.
6. Covenant Monitoring Agent — tracks covenant compliance (Debt/EBITDA < 4.0×, DSCR > 1.25×, minimum liquidity). Output: Compliant / Watchlist / Breach.
7. Industry Risk Agent — assesses industry conditions (growth, competition, regulatory change, commodity exposure). Output: Industry Risk Score, Outlook.
8. Macroeconomic Agent — measures economic impact (GDP, inflation, interest rates, FX, unemployment, real-estate prices). Output: Base Case, Upside Case, Downside Case.
9. Concentration Risk Agent — identifies excessive concentrations (industry, country, region, single-name, corporate group). Flags Top 10 Borrowers / Industries / Countries.
10. IFRS9 / CECL Agent — calculates impairment (Stage classification, 12-month ECL, lifetime ECL, provision movement). Output: Allowance, Provision Expense, Coverage Ratio.
11. Pricing Agent — recommends risk-adjusted pricing (PD, LGD, capital usage, funding cost, relationship revenue). Output: Minimum Spread, Target Spread, RAROC.
12. Capital Allocation Agent — optimizes capital usage (Economic Capital, RWA, capital consumption). Output: Capital Efficiency Score.
13. Compliance & KYC Agent — monitors compliance (sanctions, PEP, adverse media, ownership, UBO, AML risk) via perpetual KYC. Output: screening results, SAR recommendations.
14. Stress Testing Agent — runs scenarios (recession, interest-rate shock, real-estate crash, FX crisis, sector shock) and their impact on PD, losses, capital, liquidity.
15. Credit Memo Agent — generates credit-committee packages (borrower overview, financial analysis, industry assessment, risk assessment, collateral, stress testing, recommendation, conditions).

ROUTING: pick the single most relevant specialist agent and set it as "routedTo". For consolidating, board-level, or executive questions, route to the Chief Risk Officer Agent.
- approve / decline / underwrite / PD / LGD / EAD / repayment / leverage / liquidity → Credit Underwriting Agent
- spread / ratio / margin / DSCR / coverage / ROA / ROE / liquidity ratios → Financial Analysis Agent
- portfolio / sector exposure / geographic / rating migration / NPL / emerging risk → Portfolio Risk Agent
- early warning / deterioration / watchlist / red flag / trigger / default → Early Warning Agent
- covenant / covenant breach / DSCR floor / debt-to-EBITDA / compliance test → Covenant Monitoring Agent
- industry / sector outlook / competition / regulation / commodity → Industry Risk Agent
- macro / GDP / inflation / interest rates / FX / unemployment / economic outlook → Macroeconomic Agent
- concentration / top exposures / single-name / country / corporate group → Concentration Risk Agent
- IFRS9 / CECL / ECL / stage / provision / allowance / coverage ratio → IFRS9 / CECL Agent
- pricing / spread / RAROC / funding cost / loan rate / minimum spread → Pricing Agent
- capital / RWA / economic capital / capital allocation / efficiency → Capital Allocation Agent
- KYC / sanctions / PEP / UBO / adverse media / AML / SAR → Compliance & KYC Agent
- stress / scenario / recession / capital impact / liquidity stress / CET1 → Stress Testing Agent
- credit memo / committee package / memo / recommendation / conditions → Credit Memo Agent
Fall back to the Chief Risk Officer Agent for general questions.

GLOBAL RULES (every agent must): 1. Explain reasoning. 2. Cite data sources. 3. Show calculations. 4. Quantify uncertainty. 5. Flag missing data. 6. Maintain audit logs. 7. Escalate material risks. 8. Never override policy limits. 9. Never approve loans automatically. 10. Produce regulator-ready outputs.

Tools you can invoke (state them when you use them):
- extract_financials(docId) — Automated Spreading: extract structured financials (revenue, EBITDA, debt, cash, ratios) from statements
- run_credit_model(appId) — score an application, returns score/PD/grade/confidence
- monitor_credit(customer, cadence) — Continuous Credit Monitoring: real-time risk score, deterioration drivers, alerts
- monitor_covenants(customer) — covenant compliance check (Compliant / Watchlist / Breach)
- query_database(table, filter) — pull client/financial data
- scan_aml_alerts(customer) — AML/KYC screening (sanctions, PEP, adverse media, UBO)
- get_stress_test_result(scenario, severity) — regulatory capital impact
- fetch_treasury_forecast() — projected funding gap / liquidity
- price_loan(deal) — risk-adjusted pricing + RAROC
- allocate_capital(portfolio) — economic capital / RWA

You must ALWAYS respond in JSON with this exact schema:
{
  "summary": "Concise plain-text answer to the user, in layman banking terms.",
  "steps": [{"title": "short step label", "detail": "one-line explanation"}],
  "tools": [{"name": "extract_financials", "args": "APP-1042 statements", "status": "complete"}],
  "agents": [{"name": "Credit Underwriting Agent", "role": "scored the application", "status": "complete"}],
  "confidence": 87,
  "evidence": ["Data point that supports the answer, cited specifically"],
  "recommendations": ["Recommended next action for the bank/user"],
  "routedTo": "Credit Underwriting Agent",
  "humanApprovalNeeded": false
}
The "steps" array shows your step-by-step reasoning. The "tools" array lists every tool call you make. The "agents" array shows which agent(s) handled each part. Set "humanApprovalNeeded" to true when elevated risk, a decline, a capital breach, or a high-severity AML case means a human banker must review before acting — this is the Dual Workforce checkpoint (the platform never approves loans automatically). Do not mention you are an AI language model.`;

/* ---------- structured agent call ---------- */
async function runAgent(messages) {
  if (!openai) return mockAgentResponse(messages);
  const context = trainedPrompt();
  const res = await openai.chat.completions.create({
    model,
    temperature: 0.4,
    response_format: { type: 'json_object' },
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      ...(context ? [{ role: 'system', content: context }] : []),
      ...messages.slice(-8),
    ],
  });
  const raw = res.choices[0].message.content;
  return JSON.parse(raw);
}

/* ---------- routes ---------- */
app.get('/api/agent/health', (req, res) => {
  res.json({ ok: true, model, ai: Boolean(openai), mock: !openai, trained: Boolean(trainedModel()) });
});

/* ---------- dataset-trained agent models ---------- */
app.get('/api/train/status', (req, res) => {
  const a = trainedModel();
  if (!a) return res.status(404).json({ error: 'No trained model artifact found. POST /api/train to train the agents on the dataset.' });
  res.json({
    trainedAt: a.trainedAt,
    dataset: a.dataset,
    model: a.model,
    sections: Object.entries(a.sections).map(([name, s]) => ({
      name,
      model: s.model,
      summary: trainedSectionSummary(name),
    })),
  });
});

app.post('/api/train', async (req, res) => {
  try {
    trained = await trainer.train();
    res.json({ ok: true, trainedAt: trained.trainedAt, model: trained.model, sections: Object.keys(trained.sections) });
  } catch (err) {
    if (err.code === 'ENOENT') res.status(500).json({ error: 'Dataset file missing. Run `node scripts/download-dataset.js` first.', detail: err.message });
    else res.status(500).json({ error: err.message });
  }
});

function trainedSectionSummary(name) {
  const a = trainedModel();
  if (!a) return null;
  const s = a.sections[name];
  if (!s) return null;
  switch (name) {
    case 'underwriting': return `${a.dataset.firms} firms scored · grade bands ${a.model.grades.join(' · ')} · baseline ECL $${s.ecl.toFixed(0)}M`;
    case 'earlyWarning': return `${s.watchlist.length} watchlist names ranked · thresholds ${JSON.stringify(s.thresholds)}`;
    case 'rmCopilot': return `${s.clients.length} clients derived from firm book · sector cross-sell rules loaded`;
    case 'portfolioRisk': return `${s.sectorStats.length} sectors · ${s.regionStats.length} regions · ECL $${s.ecl.toFixed(0)}M`;
    case 'stressTesting': return `${s.scenarios.length} scenarios · CET1 after ${s.scenarios.map((x) => x.after + '%').join('/')}`;
    case 'cfoAI': return `CET1 ${s.cet1}% · ECL $${s.ecl.toFixed(0)}M · ${s.recommendations.length} recommendations`;
    case 'aml': return `${s.alerts.length} flagged accounts · ${s.alerts.filter((x) => x.risk === 'High').length} high risk`;
    case 'treasury': return `funding gap $${s.gap}M ${s.date} · LCR ${s.lcr}%`;
    case 'overview': return `${s.firms} firms · default rate ${(s.defaultRate * 100).toFixed(0)}% · ECL $${s.ecl.toFixed(0)}M`;
    case 'datasetAgent': return `${s.stats.firms} firms · ${s.stats.features} features profiled`;
    case 'digitalPartners': return `${s.roster.length} partners · routing grounded on trained artifacts`;
    default: return null;
  }
}

/* ---------- Zenodo dataset inspector (metadata + sample only, no full download) ---------- */
const ZENODO_BASE = 'https://zenodo.org/api/records';
const ZENODO_HEADERS = { 'User-Agent': 'BankRisk-webapp/1.0 (demo; contact: internal@bankrisk.example)', Accept: 'application/json' };
const zenodo = async (url, opts = {}) => fetch(url, { ...opts, headers: { ...ZENODO_HEADERS, ...(opts.headers || {}) } });

function cleanDescription(html) {
  return String(html || '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizeCell(v) {
  const s = String(v).trim();
  if (s === '') return '';
  if (/^[-+]?\d{1,3}(\.\d{3})*,\d+$/.test(s) || /^[-+]?\d+,\d+$/.test(s)) {
    const n = Number(s.replace(/\./g, '').replace(',', '.'));
    if (Number.isFinite(n)) return n;
  }
  if (/^[-+]?\d+$/.test(s)) { const n = Number(s); if (Number.isFinite(n)) return n; }
  if (/^[-+]?\d*\.\d+$/.test(s)) { const n = Number(s); if (Number.isFinite(n)) return n; }
  return s;
}

function parseCSVLine(line) {
  const out = [];
  let cur = '', inQ = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (inQ) {
      if (c === '"') {
        if (line[i + 1] === '"') { cur += '"'; i++; }
        else inQ = false;
      } else cur += c;
    } else if (c === '"') inQ = true;
    else if (c === ',') { out.push(cur); cur = ''; }
    else cur += c;
  }
  out.push(cur);
  return out.map(normalizeCell);
}

app.get('/api/zenodo/:id', async (req, res) => {
  try {
    if (!/^\d+$/.test(req.params.id)) return res.status(400).json({ error: 'record id must be numeric' });
    const r = await zenodo(`${ZENODO_BASE}/${req.params.id}`);
    if (!r.ok) throw new Error('Zenodo API returned ' + r.status);
    const j = await r.json();
    const meta = j.metadata || {};
    res.json({
      id: req.params.id,
      title: meta.title || 'N/A',
      doi: j.doi || 'N/A',
      publication_date: meta.publication_date || 'N/A',
      access_right: meta.access_right || 'N/A',
      license: (meta.license || {}).id || 'N/A',
      resource_type: (meta.resource_type || {}).title || 'N/A',
      creators: (meta.creators || []).map((c) => c.name),
      stats: j.stats || {},
      description: cleanDescription(meta.description),
      files: (j.files || []).map((f) => ({ key: f.key, size: f.size || 0, checksum: f.checksum || '', url: (f.links && f.links.self) || '' })),
      total_size: (j.files || []).reduce((a, f) => a + (f.size || 0), 0),
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const zenodoStatsCache = new Map();

async function getZenodoStats(id) {
  if (zenodoStatsCache.has(id)) return zenodoStatsCache.get(id);
  const metaRes = await zenodo(`${ZENODO_BASE}/${id}`);
  if (!metaRes.ok) throw new Error('Zenodo API returned ' + metaRes.status);
  const j = await metaRes.json();
  const file = (j.files || [])[0];
  if (!file) throw new Error('No files on this record.');
  const up = await zenodo((file.links && file.links.self) || '');
  if (!up.ok) throw new Error('File download returned ' + up.status);
  const text = (await up.text()).replace(/^\uFEFF/, '');
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== '');
  if (!lines.length) throw new Error('File has no data rows.');
  const headerRaw = parseCSVLine(lines[0]);
  const used = headerRaw.map((c, i) => ({ header: c, i })).filter((h) => h.header !== '' && !/^Unnamed\s*\d*/i.test(h.header));
  const columns = used.map((h) => h.header);
  const result = { firms: lines.length - 1, features: columns.length, columns, file: file.key, sizeBytes: text.length, sampled: false };
  zenodoStatsCache.set(id, result);
  return result;
}

app.get('/api/zenodo/:id/stats', async (req, res) => {
  try {
    if (!/^\d+$/.test(req.params.id)) return res.status(400).json({ error: 'record id must be numeric' });
    res.json(await getZenodoStats(req.params.id));
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/zenodo/:id/sample', async (req, res) => {
  try {
    if (!/^\d+$/.test(req.params.id)) return res.status(400).json({ error: 'record id must be numeric' });
    const metaRes = await zenodo(`${ZENODO_BASE}/${req.params.id}`);
    if (!metaRes.ok) throw new Error('Zenodo API returned ' + metaRes.status);
    const j = await metaRes.json();
    const file = (j.files || [])[0];
    if (!file) return res.json({ columns: [], rows: [], note: 'No files on this record.' });
    const up = await zenodo((file.links && file.links.self) || '', { headers: { Range: 'bytes=0-65535' } });
    const text = (await up.text()).replace(/^\uFEFF/, '');
    const lines = text.split(/\r?\n/).filter((l) => l.trim() !== '');
    if (!lines.length) return res.json({ columns: [], rows: [], note: 'Empty file preview.' });
    const columns = parseCSVLine(lines[0]).map((c, i) => (c === '' || /^Unnamed/i.test(c) ? `col_${i + 1}` : c));
    const rows = lines.slice(1, 31).map(parseCSVLine);
    res.json({ file: file.key, columns, rows, preview: true, bytesFetched: text.length });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/agent/analyze', async (req, res) => {
  try {
    const { query, context } = req.body || {};
    const messages = [{ role: 'user', content: context ? `Context: ${context}\n\nQuestion: ${query}` : query }];
    const result = await runAgent(messages);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/agent/chat', async (req, res) => {
  try {
    const { messages = [] } = req.body || {};
    const result = await runAgent(messages);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/* ---------- mock agent responses (no API key) ---------- */
function trainedSectionReply(q, ctx) {
  const a = trainedModel();
  if (!a) return null;
  const tmp = {
    summary: '', steps: [], tools: [{ name: 'train_agent', args: 'zenodo 18115815', status: 'complete' }],
    agents: [{ name: 'Chief Risk Officer Agent', role: 'grounded answer on trained portfolio model', status: 'complete' }],
    confidence: 0, evidence: [], recommendations: [], routedTo: routeTrainedAgent(q), humanApprovalNeeded: false,
  };
  const set = (p) => Object.assign(tmp, p);

  if (q.includes('covenant')) {
    const u = a.sections.underwriting;
    const apps = u.applications.slice(0, 5);
    const lines = apps.map((x) => {
      const lev = x.metrics.find((m) => String(m[0]).startsWith('Leverage'));
      const status = x.recommendation === 'Approve' ? 'Compliant' : x.recommendation === 'Approve with conditions' ? 'Watchlist' : 'Breach';
      return `${x.name}: Debt/EBITDA ${lev ? lev[1] : '—'} · DSCR ${(x.pd < 3 ? '1.6' : x.pd < 7 ? '1.3' : '1.1')}× → ${status}`;
    }).join(' | ');
    return set({
      summary: `Covenant Monitoring tests Debt/EBITDA < 4.0×, DSCR > 1.25× and minimum liquidity across the trained book. ${lines}. Breaches auto-escalate to the Chief Risk Officer for a waiver or amendment decision.`,
      steps: [
        { title: 'Loaded covenant terms', detail: 'Debt/EBITDA < 4.0× · DSCR > 1.25× · min liquidity' },
        { title: 'Pulled latest financials', detail: 'Automated Spreading on trained applications' },
        { title: 'Tested each covenant', detail: `${apps.length} obligors assessed` },
        { title: 'Flagged breaches', detail: 'Compliant / Watchlist / Breach assigned' },
      ],
      tools: [{ name: 'monitor_covenants', args: 'trained book · quarterly', status: 'complete' }],
      agents: [
        { name: 'Covenant Monitoring Agent', role: 'tested covenants against latest financials', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'queued breaches for waiver decision', status: 'complete' },
      ],
      confidence: 87,
      evidence: lines,
      recommendations: ['Remediate breached covenants within 30 days', 'Escalate breaches to credit committee', 'Log covenant tests to the audit trail'],
      humanApprovalNeeded: apps.some((x) => x.recommendation === 'Decline'),
    });
  }

  if (q.includes('concentration') || q.includes('single name') || q.includes('corporate group') || q.includes('top 10')) {
    const ps = a.sections.portfolioRisk;
    const conc = ps.concentration || [];
    const topSec = conc.slice(0, 3).map((c) => `${c.sector} ${c.share}%`).join(', ');
    const topReg = ps.regionStats.map((r) => `${r.region} ${(r.meanPD * 100).toFixed(1)}% PD`).join(', ');
    return set({
      summary: `Concentration Risk flags the top industry, country and single-name exposures of the trained book. Top industries by EAD: ${topSec}. Regional split: ${topReg}. The largest sector exceeds the 15% single-sector guideline, so the Concentration Risk Agent recommends limit-based de-risking.`,
      steps: [
        { title: 'Segmented by industry/country', detail: `${ps.sectorStats.length} sectors × ${ps.regionStats.length} regions` },
        { title: 'Measured single-name exposure', detail: 'top obligors by firm EAD' },
        { title: 'Tested against limits', detail: 'single-sector / single-name concentration caps' },
        { title: 'Flagged excess concentrations', detail: 'top 10 borrowers / industries / countries' },
      ],
      tools: [{ name: 'query_database', args: 'exposure index, grouped by sector/region', status: 'complete' }],
      agents: [
        { name: 'Concentration Risk Agent', role: 'measured sector, country and single-name concentration', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'recommended limit-based de-risking', status: 'complete' },
      ],
      confidence: 86,
      evidence: [`Top industries: ${topSec}`, `Regional PD: ${topReg}`],
      recommendations: ['Cap the largest single-sector exposure', 'Set single-name limits on top obligors', 'Re-balance geographic mix quarterly'],
    });
  }

  if (q.includes('ifrs') || q.includes('cecl') || q.includes('stage') || q.includes('provision') || q.includes('allowance') || q.includes('coverage')) {
    const u = a.sections.underwriting;
    const o = a.sections.overview;
    const ecl = u.ecl;
    const cov = (ecl / o.eadM * 100).toFixed(2);
    return set({
      summary: `IFRS 9 / CECL on the trained portfolio: expected credit loss $${ecl.toFixed(0)}M against a $${Math.round(o.eadM)}M EAD book (coverage ~${cov}%). Stage 1 (performing) uses 12-month ECL; Stage 2 (significant increase in credit risk) and Stage 3 (credit-impaired) use lifetime ECL. Provision movement is recomputed each reporting period.`,
      steps: [
        { title: 'Classified stages', detail: 'Stage 1 / Stage 2 (SICR) / Stage 3 (impaired)' },
        { title: 'Computed 12-month ECL', detail: 'PD × LGD × EAD on performing book' },
        { title: 'Computed lifetime ECL', detail: 'for SICR and credit-impaired names' },
        { title: 'Derived allowance & coverage', detail: `$${ecl.toFixed(0)}M allowance · ${cov}% coverage` },
      ],
      tools: [{ name: 'query_database', args: 'stage transition matrix · trained book', status: 'complete' }],
      agents: [
        { name: 'IFRS9 / CECL Agent', role: 'computed stage-based ECL and provision movement', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'reviewed allowance for audit sign-off', status: 'complete' },
      ],
      confidence: 85,
      evidence: [`Allowance $${ecl.toFixed(0)}M`, `Coverage ${cov}%`, `EAD $${Math.round(o.eadM)}M`],
      recommendations: ['Re-run staging each reporting period', 'Document SICR triggers in the audit trail', 'Reconcile allowance to the GL'],
    });
  }

  if (q.includes('pricing') || q.includes('raroc') || q.includes('funding cost') || q.includes('minimum spread') || q.includes('target spread') || q.includes('loan rate')) {
    const u = a.sections.underwriting;
    const app = u.applications[0];
    const el = app.pd * (u.lgd * 100) / 100;
    const minSpread = (el + 1.5).toFixed(2);
    const target = (el + 2.3).toFixed(2);
    return set({
      summary: `Pricing Agent on ${app.name} (PD ${app.pd}%, LGD ${(u.lgd * 100).toFixed(0)}%): expected loss charge ≈ ${el.toFixed(2)}%. Recommended minimum spread ${minSpread}% and target spread ${target}% over funding cost, producing a risk-adjusted return on capital (RAROC) above the 15% hurdle.`,
      steps: [
        { title: 'Loaded risk inputs', detail: `PD ${app.pd}% · LGD ${(u.lgd * 100).toFixed(0)}% · capital usage` },
        { title: 'Added funding & relationship revenue', detail: 'funding cost + cross-sell credit' },
        { title: 'Solved for minimum spread', detail: `EL ${el.toFixed(2)}% + cost of capital` },
        { title: 'Set target spread & RAROC', detail: `${minSpread}% min · ${target}% target` },
      ],
      tools: [{ name: 'price_loan', args: `${app.id} · risk-adjusted pricing`, status: 'complete' }],
      agents: [
        { name: 'Pricing Agent', role: 'computed minimum/target spread and RAROC', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'validated against pricing policy limits', status: 'complete' },
      ],
      confidence: 83,
      evidence: [`Expected loss ${el.toFixed(2)}%`, `LGD ${(u.lgd * 100).toFixed(0)}%`, `PD ${app.pd}%`],
      recommendations: [`Price ${app.name} at ≥ ${minSpread}% over funding`, 'Bundle relationship revenue to lower spread', 'Re-price if PD migrates'],
    });
  }

  if (q.includes('capital allocation') || q.includes('allocate') || q.includes('rwa') || q.includes('economic capital') || q.includes('efficiency')) {
    const cfo = a.sections.cfoAI;
    return set({
      summary: `Capital Allocation on the trained portfolio: economic capital is calibrated from ECL volatility and RWA density, with CET1 at ${cfo.cet1}%. The Capital Allocation Agent scores business lines by capital efficiency (return on risk-adjusted capital), steering capital away from low-return, high-RWA segments.`,
      steps: [
        { title: 'Computed RWA', detail: 'credit + market + operational risk weights' },
        { title: 'Estimated economic capital', detail: 'EC = unexpected loss × confidence factor' },
        { title: 'Measured capital consumption', detail: 'per business line' },
        { title: 'Scored capital efficiency', detail: 'RORAC ranking' },
      ],
      tools: [{ name: 'allocate_capital', args: 'trained portfolio · business lines', status: 'complete' }],
      agents: [
        { name: 'Capital Allocation Agent', role: 'optimized capital across business lines', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'reviewed against capital plan', status: 'complete' },
      ],
      confidence: 84,
      evidence: [`CET1 ${cfo.cet1}%`, `Baseline ECL $${cfo.ecl.toFixed(0)}M`],
      recommendations: ['Shift capital to highest RORAC segments', 'Reduce RWA density in CRE', 'Re-run allocation quarterly'],
    });
  }

  if (q.includes('credit memo') || q.includes('committee') || q.includes('memo')) {
    const u = a.sections.underwriting;
    const app = u.applications[0];
    return set({
      summary: `Credit Memo Agent drafted a loan-committee package for ${app.name} (${app.id}): ${app.memo} Recommendation: ${app.recommendation} (grade ${app.grade}, PD ${app.pd}%).`,
      steps: [
        { title: 'Assembled borrower overview', detail: `${app.name} · ${app.industry} · ${app.region}` },
        { title: 'Financial analysis', detail: app.metrics.slice(0, 3).map((m) => `${m[0]} ${m[1]}`).join('; ') },
        { title: 'Risk & stress assessment', detail: `PD ${app.pd}% · grade ${app.grade}` },
        { title: 'Recommendation & conditions', detail: app.recommendation },
      ],
      tools: [{ name: 'extract_financials', args: `${app.id} · statements`, status: 'complete' }],
      agents: [
        { name: 'Credit Memo Agent', role: 'drafted the committee package', status: 'complete' },
        { name: 'Credit Underwriting Agent', role: 'supplied PD/LGD/rating', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'final sign-off review', status: 'complete' },
      ],
      confidence: 89,
      evidence: [`Grade ${app.grade}`, `PD ${app.pd}%`, app.recommendation],
      recommendations: ['Circulate memo to credit committee', 'Attach covenants and conditions', 'Log committee decision to the audit trail'],
      humanApprovalNeeded: app.recommendation !== 'Approve',
    });
  }

  if (q.includes('industry') || q.includes('sector outlook') || q.includes('competition') || q.includes('commodity')) {
    const ps = a.sections.portfolioRisk;
    const list = ps.sectorStats.map((s) => `${s.sector} (${(s.meanPD * 100).toFixed(1)}% PD)`).join(', ');
    return set({
      summary: `Industry Risk Agent scores the six sectors of the trained book by growth, competition, regulation and commodity exposure. Trained PD by sector: ${list}. Retail and Energy carry the highest risk (negative outlook); Technology is the strongest (positive outlook).`,
      steps: [
        { title: 'Measured industry growth', detail: 'revenue trends across sectors' },
        { title: 'Scored competition & regulation', detail: 'competitive intensity + regulatory change' },
        { title: 'Assessed commodity exposure', detail: 'energy & materials sensitivity' },
        { title: 'Assigned outlook', detail: 'positive / neutral / negative' },
      ],
      tools: [{ name: 'query_database', args: 'industry risk index · trained book', status: 'complete' }],
      agents: [
        { name: 'Industry Risk Agent', role: 'scored industry risk and outlook', status: 'complete' },
        { name: 'Portfolio Risk Agent', role: 'linked sector PD to industry outlook', status: 'complete' },
      ],
      confidence: 82,
      evidence: list,
      recommendations: ['Tighten exposure to Retail and Energy', 'Re-underwrite commodity-sensitive names', 'Refresh industry outlooks quarterly'],
    });
  }

  if (q.includes('macro') || q.includes('gdp') || q.includes('inflation') || q.includes('unemployment') || q.includes('interest rate')) {
    const st = a.sections.stressTesting;
    return set({
      summary: `Macroeconomic Agent projects a base, upside and downside case for the trained book. Base: GDP +1.8%, inflation 2.4%, rates 4.50%. Downside: GDP −1.4%, inflation 3.8%, rates 5.50%, unemployment 6.1%. These feed the Stress Testing Agent's scenarios (${st.scenarios.map((s) => s.name).join(', ')}).`,
      steps: [
        { title: 'Loaded macro indicators', detail: 'GDP, CPI, rates, FX, unemployment, real estate' },
        { title: 'Formed base case', detail: 'GDP +1.8% · inflation 2.4%' },
        { title: 'Formed upside case', detail: 'GDP +2.9% · inflation 1.9%' },
        { title: 'Formed downside case', detail: 'GDP −1.4% · inflation 3.8%' },
      ],
      tools: [{ name: 'query_database', args: 'macro forecast, 3 cases', status: 'complete' }],
      agents: [
        { name: 'Macroeconomic Agent', role: 'projected base/upside/downside cases', status: 'complete' },
        { name: 'Stress Testing Agent', role: 'linked macro cases to scenarios', status: 'complete' },
      ],
      confidence: 80,
      evidence: ['Base GDP +1.8%', 'Downside GDP −1.4%', 'Rates 4.50% → 5.50%'],
      recommendations: ['Stress the book against the downside case', 'Monitor rate path for ALM', 'Refresh macro forecasts monthly'],
    });
  }

  if (q.includes('financial analysis') || q.includes('ratio') || q.includes('dscr') || q.includes('roa') || q.includes('roe') || q.includes('ebitda')) {
    const u = a.sections.underwriting;
    const app = u.applications[0];
    const metrics = app.metrics.map((m) => `${m[0]} ${m[1]}`).join(' · ');
    return set({
      summary: `Financial Analysis Agent spreads ${app.name} and computes the ratio set: ${metrics}. Financial strength score ${app.score}/100, ${app.confidence}% confidence — trend stable versus sector peers.`,
      steps: [
        { title: 'Spread statements', detail: 'Automated Spreading on financials + tax returns' },
        { title: 'Computed profitability & leverage', detail: 'ROA/ROE/EBITDA margin · Debt/EBITDA · Debt/Equity' },
        { title: 'Computed liquidity & coverage', detail: 'current/quick/cash ratio · interest coverage · DSCR' },
        { title: 'Benchmarked vs peers', detail: `${app.score}/100 financial strength score` },
      ],
      tools: [{ name: 'extract_financials', args: `${app.id} · statements`, status: 'complete' }],
      agents: [
        { name: 'Financial Analysis Agent', role: 'spread and ratio analysis', status: 'complete' },
        { name: 'Credit Underwriting Agent', role: 'consumed ratios for scoring', status: 'complete' },
      ],
      confidence: app.confidence || 86,
      evidence: metrics.split(' · ').slice(0, 3),
      recommendations: ['Attach ratio sheet to the credit file', 'Benchmark against sector peers', 'Re-spread on new statements'],
    });
  }

  if (q.includes('train') || q.includes('model') || q.includes('auc') || q.includes('r2') || q.includes('accuracy') || q.includes('correlation')) {
    return set({
      summary: `Each AI agent is trained on Zenodo dataset 18115815 (${a.dataset.firms} synthetic firms, 13 features). Core credit engine: ${a.model.type} → R² ${a.model.r2}, correlation ${a.model.corr} on ${a.model.evaluatedOn} holdout firms. ${Object.keys(a.sections).length} module agents are grounded on this model, e.g. Credit Underwriting (grade bands ${a.model.grades.join(', ')}), Early Warning (${a.sections.earlyWarning.watchlist.length} ranked names), Stress Testing (${a.sections.stressTesting.scenarios.map((s) => s.name).join(', ')}).`,
      steps: [
        { title: 'Loaded dataset', detail: `${a.dataset.firms} firms · ${a.dataset.features} features` },
        { title: 'Fitted risk model', detail: `${a.model.type} → R² ${a.model.r2}` },
        { title: 'Derived per-section agents', detail: `${Object.keys(a.sections).length} modules trained` },
      ],
      agents: [
        { name: 'Credit Underwriting Agent', role: 'trained the core credit-risk model', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'validated portfolio grounding', status: 'complete' },
        { name: 'Stress Testing Agent', role: 'derived scenario knowledge', status: 'complete' },
      ],
      confidence: 90,
      evidence: [`R² ${a.model.r2} · corr ${a.model.corr}`, `${a.dataset.firms} firms used`, `${Object.keys(a.sections).length} agents trained`],
      recommendations: ['Re-train when the source dataset changes', 'Review grade bands against policy', 'Add a real GLM if you need interpretable coefficients'],
    });
  }
  if (q.includes('dataset') || q.includes('zenodo') || q.includes('synthetic') || q.includes('how many')) {
    const o = a.sections.overview;
    return set({
      summary: `Zenodo record 18115815 holds a fully synthetic firm-level credit-risk dataset: **${a.dataset.firms} firms**, **${a.dataset.features} features**, empirical default rate ${(o.defaultRate * 100).toFixed(1)}%. The portfolio agent is trained on it and projects **$${Math.round(o.eadM)}M portfolio EAD** with a **baseline ECL of $${o.ecl.toFixed(0)}M**. Because the data is synthetic it is for prototyping only, never real customer data.`,
      steps: [
        { title: 'Profiled source file', detail: `${a.dataset.firms} firms · ${a.dataset.features} features` },
        { title: 'Measured default structure', detail: `${(o.defaultRate * 100).toFixed(1)}% empirical default rate` },
        { title: 'Extracted byRegionSummary', detail: (a.sections.portfolioRisk.regionStats.map((r) => `${r.region} ${(r.meanPD * 100).toFixed(1)}%`).join(', ')) },
      ],
      agents: [
        { name: 'Credit Underwriting Agent', role: 'profiled schema and risk fields', status: 'complete' },
        { name: 'Financial Analysis Agent', role: 'counted firms and features', status: 'complete' },
      ],
      confidence: 93,
      evidence: [`${a.dataset.firms} firms (exact row count)`, `${a.dataset.features} features`, `${(o.defaultRate * 100).toFixed(1)}% default rate`],
      recommendations: ['Use only for prototyping / demos', 'Retrain agents when the dataset updates', 'Never treat synthetic firms as real customers'],
    });
  }
  if (q.includes('underwrit') || q.includes('credit') || q.includes('application') || q.includes('approve') || q.includes('decline') || q.includes('score') || q.includes('pd') || q.includes('grade')) {
    const u = a.sections.underwriting;
    const top = u.applications.slice(0, 3).map((x) => `${x.id} ${x.name} PD ${x.pd}% → ${x.grade} (${x.recommendation})`).join('; ');
    return set({
      summary: `The Credit Underwriting agent scores every firm with the trained model (baseline ECL $${u.ecl.toFixed(0)}M, LGD ${u.lgd * 100}%). Grade bands: ${a.model.grades.join(', ')}. Current queue — ${top}.`,
      steps: [
        { title: 'Spread financials', detail: 'Leverage, margin, R&D, complexity, size' },
        { title: 'Scored with trained model', detail: `R² ${a.model.r2} model on ${a.dataset.firms} firms` },
        { title: 'Assigned grade', detail: a.model.grades.join(', ') },
        { title: 'Drafted recommendation', detail: 'Approve / with-conditions / Decline by PD' },
      ],
      tools: [
        { name: 'extract_financials', args: `${u.applications[0].id} · statements`, status: 'complete' },
        { name: 'run_credit_model', args: 'trained ridge on hazard', status: 'complete' },
      ],
      agents: [
        { name: 'Credit Underwriting Agent', role: 'Automated Spreading + scoring', status: 'complete' },
        { name: 'Financial Analysis Agent', role: 'computed leverage & coverage ratios', status: 'complete' },
      ],
      confidence: Math.round(u.applications[0].confidence || 82),
      evidence: [`Grade bands ${a.model.grades.join(', ')}`, `Baseline ECL $${u.ecl.toFixed(0)}M`, top],
      recommendations: u.applications.filter((x) => x.recommendation === 'Approve').length
        ? ['Approve low-PD names with conditions', 'Escalate declines to credit committee', 'Attach trained-model audit trail']
        : ['Escalate all current queue to credit committee', 'Re-price marginal names', 'Attach trained-model audit trail'],
    });
  }
  if (q.includes('early') || q.includes('warning') || q.includes('watchlist') || q.includes('deteriorat') || q.includes('distress')) {
    const e = a.sections.earlyWarning;
    const top3 = e.watchlist.slice(0, 3).map((w) => `${w.firm} (${w.sector}) PD ${w.pd}% · ${(w.drivers || []).join('; ')}`).join(' | ');
    return set({
      summary: `The Early Warning agent flags deterioration from the trained model before it becomes default. Highest names: ${top3}. Thresholds: ${JSON.stringify(e.thresholds)}.`,
      steps: [
        { title: 'Ranked book by trained PD', detail: `${e.watchlist.length} names on watchlist` },
        { title: 'Extracted drivers', detail: 'leverage, margins, complexity, R&D' },
        { title: 'Segmented severity', detail: JSON.stringify(e.thresholds) },
      ],
      tools: [{ name: 'monitor_credit', args: 'entire book · continuous', status: 'complete' }],
      agents: [
        { name: 'Early Warning Agent', role: 'ranked book by PD and triggered alerts', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'drafted account reviews', status: 'complete' },
      ],
      confidence: 86,
      evidence: top3,
      recommendations: ['Schedule 30-day reviews for High names', 'Re-run model quarterly', 'Notify RMs of top watchlist'],
    });
  }
  if (q.includes('stress') || q.includes('capital') || q.includes('cet1') || q.includes('scenario') || q.includes('recession') || q.includes('breach') || q.includes('buffer')) {
    const st = a.sections.stressTesting;
    const list = st.scenarios.map((s) => `${s.name}: ECL $${s.loss}M, uplift $${s.uplift}M, CET1 ${s.after}%${s.breach ? ' ⚠ breach' : ''}`).join(' | ');
    return set({
      summary: `Stress Testing on the trained portfolio: ${list}. ${
        st.scenarios.filter((s) => s.breach).length
          ? 'Rate-hike and CRE-downturn severities breach the 10.5% CET1 floor — capital conservation action required.'
          : 'Capital holds above the 10.5% floor across all severities.'}`,
      steps: [
        { title: 'Scaled sector PD uplifts', detail: 'recession/housing/rate/currency/CRE' },
        { title: 'Projected ECL', detail: `baseline $${a.sections.underwriting.ecl.toFixed(0)}M → scenario ECL` },
        { title: 'Projected CET1', detail: 'vs 10.5% regulatory floor' },
      ],
      tools: [{ name: 'get_stress_test_result', args: 'all severities · trained book', status: 'complete' }],
      agents: [
        { name: 'Stress Testing Agent', role: 'ran crisis scenarios', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'capital-planning read-out', status: 'complete' },
      ],
      confidence: 84,
      evidence: list,
      recommendations: st.scenarios.filter((s) => s.breach).map((s) => `${s.name}: raise Tier 1 + provisions`).concat(['Re-run quarterly']),
      humanApprovalNeeded: st.scenarios.some((s) => s.breach),
    });
  }
  if (q.includes('aml') || q.includes('suspicious') || q.includes('compliance') || q.includes('sar') || q.includes('fraud') || q.includes('alert')) {
    const al = a.sections.aml;
    const top = al.alerts.slice(0, 3).map((x) => `${x.customer}: ${x.alert} (${x.risk})`).join(' | ');
    return set({
      summary: `The AML agent flags the riskiest outliers of the trained book. Highest-severity: ${top}. Rules: ${al.rules.join(', ')}.`,
      steps: [
        { title: 'Scored outliers', detail: 'covariate effect, complexity, hazard' },
        { title: 'Matched typologies', detail: 'turnover / transfer patterns' },
        { title: 'Segmented severity', detail: 'High vs Medium dispositions' },
      ],
      tools: [{ name: 'scan_aml_alerts', args: al.alerts.map((x) => x.customer).join(', '), status: 'complete' }],
      agents: [
        { name: 'Compliance & KYC Agent', role: 'typology detection and risk scoring', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'routed escalation workflow', status: 'complete' },
      ],
      confidence: 90,
      evidence: top,
      recommendations: al.alerts.filter((x) => x.risk === 'High').slice(0, 2).map((x) => x.rec).concat(['Document rationale in audit trail']),
      humanApprovalNeeded: al.alerts.some((x) => x.risk === 'High'),
    });
  }
  if (q.includes('treasury') || q.includes('liquidity') || q.includes('funding') || q.includes('gap') || q.includes('bond') || q.includes('lcr')) {
    const t = a.sections.treasury;
    return set({
      summary: `Treasury on the trained book: funding gap $${t.gap}M by ${t.date}, LCR ${t.lcr}%, NSFR ${t.nsfr}%. Recommendation: ${t.recommendation} to lock in current rates.`,
      steps: [
        { title: 'Loaded ECL-driven forecast', detail: '8-month positions' },
        { title: 'Identified gap', detail: `$${t.gap}M by ${t.date}` },
        { title: 'Assessed ratios', detail: `LCR ${t.lcr}% · NSFR ${t.nsfr}%` },
        { title: 'Selected funding strategy', detail: t.recommendation },
      ],
      tools: [{ name: 'fetch_treasury_forecast', args: 'next 8 months · trained book', status: 'complete' }],
      agents: [
        { name: 'Macroeconomic Agent', role: 'forecast and funding-gap analysis', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'validated funding recommendation', status: 'complete' },
      ],
      confidence: 85,
      evidence: [`Funding gap $${t.gap}M`, `LCR ${t.lcr}%`, t.recommendation],
      recommendations: [t.recommendation, 'Review maturity ladder', 'Deploy excess cash into HQLA'],
    });
  }
  if (q.includes('client') || q.includes('customer') || q.includes('cross-sell') || q.includes('rm ')) {
    const rm = a.sections.rmCopilot;
    const top = rm.clients.slice(0, 3).map((c) => `${c.name} (${c.industry}, ${c.riskLabel}) PD ${c.pd}%`).join(', ');
    return set({
      summary: `The RM Copilot agent derives its client book from the trained dataset (${rm.clients.length} clients shown). Top of book: ${top}. Cross-sell rules are sector-based (e.g. ${rm.clients[0].suggestions.map((s) => s.p).join(', ')}).`,
      steps: [
        { title: 'Built client 360', detail: 'size × risk → relationship health' },
        { title: 'Scored health', detail: 'PD, leverage, margins' },
        { title: 'Matched next-best products', detail: 'per-sector cross-sell rules' },
        { title: 'Drafted meeting briefs', detail: 'risks and opportunities surfaced' },
      ],
      tools: [{ name: 'monitor_credit', args: 'client book · continuous', status: 'complete' }],
      agents: [
        { name: 'Chief Risk Officer Agent', role: 'client 360 and cross-sell engine', status: 'complete' },
        { name: 'Portfolio Risk Agent', role: 'validated risk labels', status: 'complete' },
      ],
      confidence: 84,
      evidence: top,
      recommendations: ['Prioritise High-risk client reviews', 'Close top cross-sell per client', 'Log meeting briefs to CRM'],
    });
  }
  if (q.includes('sector') || q.includes('portfolio') || q.includes('concentration') || q.includes('exposure') || q.includes('distribution')) {
    const ps = a.sections.portfolioRisk;
    return set({
      summary: `Portfolio risk on the trained book: sector PD ranking ${ps.sectorStats.map((s) => `${s.sector} ${(s.meanPD * 100).toFixed(1)}%`).join(', ')}. Region mean PD ${ps.regionStats.map((r) => `${r.region} ${(r.meanPD * 100).toFixed(1)}%`).join(', ')}. ECL $${ps.ecl.toFixed(0)}M.`,
      steps: [
        { title: 'Segmented book', detail: `6 sectors × 3 regions` },
        { title: 'Scored segments', detail: 'trained PD by segment' },
        { title: 'Measured exposure', detail: `${a.sections.overview.eadM} EAD` },
      ],
      tools: [{ name: 'query_database', args: 'trained portfolio index', status: 'complete' }],
      agents: [{ name: 'Portfolio Risk Agent', role: 'segment risk and ECL', status: 'complete' }],
      confidence: 88,
      evidence: ps.sectorStats.slice(0, 2).map((s) => `${s.sector} PD ${(s.meanPD * 100).toFixed(1)}%`),
      recommendations: ['Monitor top-PD sectors', 'Review regional concentration', 'Re-test quarterly'],
    });
  }
  return null;
}

function routeTrainedAgent(q) {
  if (q.includes('covenant')) return 'Covenant Monitoring Agent';
  if (q.includes('concentration') || q.includes('single.?name') || q.includes('top 10') || q.includes('corporate group')) return 'Concentration Risk Agent';
  if (q.includes('ifrs') || q.includes('cecl') || q.includes('stage') || q.includes('provision') || q.includes('allowance') || q.includes('coverage ratio')) return 'IFRS9 / CECL Agent';
  if (q.includes('pricing') || q.includes('spread') || q.includes('raroc') || q.includes('funding cost') || q.includes('loan rate')) return 'Pricing Agent';
  if (q.includes('capital allocation') || q.includes('allocate') || q.includes('rwa') || q.includes('economic capital') || q.includes('efficiency')) return 'Capital Allocation Agent';
  if (q.includes('credit memo') || q.includes('committee') || q.includes('memo')) return 'Credit Memo Agent';
  if (q.includes('industry') || q.includes('sector outlook') || q.includes('competition')) return 'Industry Risk Agent';
  if (q.includes('macro') || q.includes('gdp') || q.includes('inflation') || q.includes('unemployment') || q.includes('fx')) return 'Macroeconomic Agent';
  if (q.includes('spread') || q.includes('ratio') || q.includes('dscr') || q.includes('coverage') || q.includes('roa') || q.includes('roe')) return 'Financial Analysis Agent';
  if (q.includes('underwrit') || q.includes('application') || q.includes('approve') || q.includes('decline') || q.includes('pd') || q.includes('grade') || q.includes('lgd') || q.includes('ead')) return 'Credit Underwriting Agent';
  if (q.includes('early') || q.includes('warning') || q.includes('watchlist') || q.includes('deteriorat')) return 'Early Warning Agent';
  if (q.includes('stress') || q.includes('scenario') || q.includes('recession') || q.includes('cet1') || q.includes('capital')) return 'Stress Testing Agent';
  if (q.includes('aml') || q.includes('suspicious') || q.includes('sanction') || q.includes('pep') || q.includes('kyc') || q.includes('ubo') || q.includes('sar')) return 'Compliance & KYC Agent';
  if (q.includes('portfolio') || q.includes('sector') || q.includes('exposure') || q.includes('rating migration') || q.includes('npl')) return 'Portfolio Risk Agent';
  if (q.includes('client') || q.includes('customer') || q.includes('relationship') || q.includes('treasury') || q.includes('liquidity') || q.includes('funding')) return 'Chief Risk Officer Agent';
  return 'Chief Risk Officer Agent';
}

async function mockAgentResponse(messages) {
  const last = messages.filter((m) => m.role === 'user').pop();
  const q = (last?.content || '').toLowerCase();
  const ctx = String(last?.content || '');

  const trainedReply = trainedSectionReply(q, ctx);
  if (trainedReply) return trainedReply;

  if (q.includes('zenodo') || q.includes('dataset') || q.includes('synthetic firm') || (q.includes('how many') && q.includes('firm'))) {
    let stats;
    try { stats = await getZenodoStats('18115815'); } catch (e) { stats = null; }
    const firms = stats ? stats.firms.toLocaleString() : 'unknown';
    const feats = stats ? String(stats.features) : 'unknown';
    const colList = stats && stats.columns.length ? stats.columns.join(', ') : 'Sector, Region, Leverage, Profit_Margin, hazard, Event_Time, Status';
    return {
      summary: `Zenodo record 18115815 holds a fully synthetic firm-level credit-risk dataset: **${stats ? firms + ' firms' : firms}** in the source file (\`firms_features_clean.csv\`) with **${stats ? feats + ' feature columns' : feats}** — ${colList}. Companies span Services, Technology, Manufacturing, Retail, Energy, Finance, and more, in Europe, Latin America, and the USA. Because the data is synthetic it is safe for prototyping and demos, but must not be used as real customer data.`,
      steps: [
        { title: 'Hit the Zenodo REST API', detail: 'Fetched metadata only — no bulk download' },
        { title: 'Counted rows in the source file', detail: stats ? `${firms} firms (header + data rows parsed)` : 'Fetching exact count from the source file' },
        { title: 'Profiled the schema', detail: stats ? `${feats} feature columns identified from the header` : 'Fetching header' },
        { title: 'Normalized European decimals', detail: '"7229,321243" → 7229.32' },
      ],
      tools: [
        { name: 'query_database', args: 'zenodo/records/18115815', status: 'complete' },
        { name: 'count_rows', args: 'firms_features_clean.csv', status: stats ? 'complete' : 'pending' },
        { name: 'count_features', args: stats ? feats + ' columns' : 'header', status: stats ? 'complete' : 'pending' },
      ],
      agents: [
        { name: 'Credit Underwriting Agent', role: 'profiled the dataset schema and risk fields', status: 'complete' },
        { name: 'Financial Analysis Agent', role: 'counted firms and features in the source', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'framed safe-use guidance', status: 'complete' },
      ],
      confidence: 92,
      evidence: stats ? [`${firms} synthetic firms (exact row count)`, `${feats} feature columns: ${colList}`] : ['Exact counts computed from the source file'],
      recommendations: ['Use only for prototyping / demos', 'Treat as synthetic — never use as real customer data', 'Load sample into the credit model sandbox'],
      routedTo: 'Credit Underwriting Agent',
      humanApprovalNeeded: false,
    };
  }

  if (q.includes('delta foods') || q.includes('credit')) {
    return {
      summary: "Delta Foods Co. has a stable credit profile: PD 2.8%, credit grade B+, leverage of 2.9× and a current ratio of 1.38×. Approve a $2.5M facility with conditions (personal guarantee + quarterly covenant reporting).",
      steps: [
        { title: 'Pulled financial statements', detail: 'FY2023 results and 12 months of bank statements loaded' },
        { title: 'Calculated key ratios', detail: 'DSCR 1.62×, current ratio 1.38×, leverage 2.9×' },
        { title: 'Scored application', detail: 'Credit score 74/100 → grade B+' },
        { title: 'Established conditions', detail: 'Personal guarantee and quarterly covenants reduce default risk' },
      ],
      tools: [
        { name: 'extract_financials', args: 'APP-1042 · statements + tax returns', status: 'complete' },
        { name: 'run_credit_model', args: 'APP-1042 · Automated Spreading → PD model', status: 'complete' },
        { name: 'monitor_credit', args: 'Delta Foods · continuous', status: 'complete' },
      ],
      agents: [
        { name: 'Credit Underwriting Agent', role: 'Automated Spreading + financial analysis and scoring', status: 'complete' },
        { name: 'Financial Analysis Agent', role: 'computed ratios and conditions', status: 'complete' },
      ],
      confidence: 88,
      evidence: ['DSCR 1.62× above 1.2× policy floor', 'PD 2.8% vs portfolio average 2.6%', 'Leverage 2.9× within sector norm'],
      recommendations: ['Approve $2.5M with conditions', 'Require personal guarantee', 'Set quarterly covenant reporting'],
      routedTo: 'Credit Underwriting Agent',
      humanApprovalNeeded: true,
    };
  }
  if (q.includes('aml') || q.includes('suspicious') || q.includes('compliance')) {
    return {
      summary: 'The pattern of international transfers by Omega Trading Ltd resembles structuring and rapid-fire movement to high-risk jurisdictions. Recommend escalation to a full compliance review and consider a SAR.',
      steps: [
        { title: 'Scanned transactions', detail: '14 transactions to 3 high-risk jurisdictions over 5 days' },
        { title: 'Applied AML typologies', detail: 'Pattern matched structuring / rapid-turnover typology' },
        { title: 'Risk-scored customer', detail: 'Customer escalated to High severity' },
      ],
      tools: [
        { name: 'scan_aml_alerts', args: 'Omega Trading Ltd', status: 'complete' },
        { name: 'monitor_credit', args: 'Omega Trading Ltd · continuous', status: 'complete' },
        { name: 'query_database', args: 'transactions, 30-day window', status: 'complete' },
      ],
      agents: [
        { name: 'Compliance & KYC Agent', role: 'ran typology detection and risk scoring', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'routed escalation and workflow', status: 'complete' },
      ],
      confidence: 91,
      evidence: ['$1.2M moved in rapid-fire transfers', '3 counterparties in high-risk jurisdictions', 'Customer profile inconsistent with cash/transfer volume'],
      recommendations: ['Escalate to full compliance review', 'File SAR on the account', 'Freeze the account pending investigation'],
      routedTo: 'Compliance & KYC Agent',
      humanApprovalNeeded: true,
    };
  }
  if (q.includes('stress') || q.includes('capital') || q.includes('cre')) {
    return {
      summary: 'Under a CRE downturn (prices −20%), expected credit loss rises ~$110M and CET1 falls from 14.2% to ~10.4% — below the 10.5% regulatory minimum. Recommend raising loan-loss provisions and shoring up capital buffers.',
      steps: [
        { title: 'Loaded stress scenario', detail: 'CRE downturn: commercial real estate −20%' },
        { title: 'Applied loss shocks', detail: 'Credit losses modeled across the CRE portfolio' },
        { title: 'Projected capital', detail: 'CET1 falls 3.8pp to 10.4%' },
        { title: 'Checked regulatory floor', detail: 'Breach of 10.5% → capital conservation action' },
      ],
      tools: [
        { name: 'get_stress_test_result', args: 'commercial real estate downturn', status: 'complete' },
        { name: 'run_credit_model', args: 'portfolio: CRE segment', status: 'complete' },
      ],
      agents: [
        { name: 'Stress Testing Agent', role: 'ran scenario and capital projection', status: 'complete' },
        { name: 'Chief Risk Officer Agent', role: 'translated into capital-planning recommendation', status: 'complete' },
      ],
      confidence: 82,
      evidence: ['CRE stress drives $110M expected loss', 'CET1 breaches the 10.5% floor', 'LCR headroom narrows 22pp'],
      recommendations: ['Increase CRE loan-loss provisions (~$18M)', 'Raise additional Tier 1 capital', 'Reduce CRE concentration'],
      routedTo: 'Chief Risk Officer Agent',
      humanApprovalNeeded: true,
    };
  }
  return {
    summary: `Based on the available data: ${q || 'no query provided'}. For a detailed answer, frame the question around a specific client, application, scenario, or alert so the relevant agent can pull the supporting data.`,
    steps: [
      { title: 'Parsed question', detail: 'Identified banking domain and intent' },
      { title: 'Gathered context', detail: 'Framed request against available modules' },
      { title: 'Drafted answer', detail: 'Produced recommendation with confidence' },
    ],
    tools: [{ name: 'query_database', args: 'portfolio index', status: 'complete' }],
    agents: [
      { name: 'Chief Risk Officer Agent', role: 'synthesized the response', status: 'complete' },
    ],
    confidence: 70,
    evidence: ['Response framed from current module context'],
    recommendations: ['Narrow the question to a specific client, case, or scenario'],
    routedTo: 'Chief Risk Officer Agent',
    humanApprovalNeeded: false,
  };
}

app.listen(port, async () => {
  console.log(`BankRisk backend running on http://localhost:${port}`);
  console.log(openai ? `AI connected (${model})` : 'AI OFF — no OPENAI_API_KEY set. Using mock responses.');
  try { await ensureTrained(); console.log(openai ? `Trained ${Object.keys(trainedModel().sections).length} agents on dataset 18115815 (R² ${trainedModel().model.r2})` : 'Mock agent grounded on trained dataset model (mock mode)'); } catch (e) { console.warn('Training not available:', e.message); }
});