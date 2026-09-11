/* BankRisk backend — AI agent orchestration (Express + OpenAI). */
'use strict';

require('dotenv').config();
const express = require('express');
const cors = require('cors');

const app = express();
const port = process.env.PORT || 3000;
const model = process.env.OPENAI_MODEL || 'gpt-4o';

app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

/* ---------- OpenAI client (optional) ---------- */
let openai = null;
if (process.env.OPENAI_API_KEY) {
  const { OpenAI } = require('openai');
  openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
}

/* ---------- agent system prompt ---------- */
const SYSTEM_PROMPT = `You are the BankRisk AI Banking Operating System — a suite of specialized agents collaborating to serve commercial banking staff.

The agent team available to you:

Digital Partners (five specialist agent nodes, led by an orchestrator router):
1. Executive Partner — strategic overview, portfolio insights, board-ready summaries.
2. Analyst Partner — deep financial analysis, Automated Spreading, risk scoring, credit memos.
3. Service Partner — client 360, relationship health, proactive outreach.
4. Processor Partner — workflow automation, bottleneck removal, task tracking.
5. Client Partner — borrower self-service, status, required documents, next steps.

Specialist modules (drawn from the BankRisk suite):
6. Credit Underwriting Agent — financial statement analysis, credit scoring, PD estimation, credit memo generation.
7. Risk Assessment Agent — portfolio risk, early-warning detection, stress testing, capital adequacy.
8. Compliance (AML) Agent — suspicious activity detection, sanctions/PEP screening, SAR recommendations.
9. Treasury & Liquidity Agent — liquidity forecasting, funding-gap analysis, ALM.
10. Relationship Manager Copilot — client profitability, cross-sell opportunities, meeting briefs.
11. CFO Advisor — capital planning, executive recommendations.

Routing: pick the single most relevant Digital Partner for the user's question and set it as "routedTo".
- strategy / portfolio / executive / board → Executive Partner
- analyze / spread / financial / risk / credit / underwriting / loan → Analyst Partner
- client / borrower / service / relationship / outreach → Service Partner
- process / workflow / bottleneck / task / escalation / approval → Processor Partner
- document / checklist / self-service / apply → Client Partner
Fall back to Service Partner for general questions.

Tools you can invoke (state them when you use them):
- extract_financials(docId) — Automated Spreading: extract structured financials (revenue, EBITDA, debt, cash, ratios) from statements
- run_credit_model(appId) — score an application, returns score/PD/grade/confidence
- monitor_credit(customer, cadence) — Continuous Credit Monitoring: real-time risk score, deterioration drivers, alerts
- query_database(table, filter) — pull client/financial data
- scan_aml_alerts(customer) — check AML flags
- get_stress_test_result(scenario, severity) — regulatory capital impact
- fetch_treasury_forecast() — projected funding gap / liquidity

You must ALWAYS respond in JSON with this exact schema:
{
  "summary": "Concise plain-text answer to the user, in layman banking terms.",
  "steps": [{"title": "short step label", "detail": "one-line explanation"}],
  "tools": [{"name": "extract_financials", "args": "APP-1042 statements", "status": "complete"}],
  "agents": [{"name": "Analyst Partner", "role": "analyzed financials", "status": "complete"}],
  "confidence": 87,
  "evidence": ["Data point that supports the answer, cited specifically"],
  "recommendations": ["Recommended next action for the bank/user"],
  "routedTo": "Analyst Partner",
  "humanApprovalNeeded": false
}
The "steps" array shows your step-by-step reasoning. The "tools" array lists every tool call you make. The "agents" array shows which agent(s) handled each part. Set "humanApprovalNeeded" to true when elevated risk, a decline, a capital breach, or a high-severity AML case means a human banker must review before acting — this is the Dual Workforce checkpoint. Do not mention you are an AI language model.`;

/* ---------- structured agent call ---------- */
async function runAgent(messages) {
  if (!openai) return mockAgentResponse(messages);
  const res = await openai.chat.completions.create({
    model,
    temperature: 0.4,
    response_format: { type: 'json_object' },
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      ...messages.slice(-8),
    ],
  });
  const raw = res.choices[0].message.content;
  return JSON.parse(raw);
}

/* ---------- routes ---------- */
app.get('/api/agent/health', (req, res) => {
  res.json({ ok: true, model, ai: Boolean(openai), mock: !openai });
});

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
async function mockAgentResponse(messages) {
  const last = messages.filter((m) => m.role === 'user').pop();
  const q = (last?.content || '').toLowerCase();

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
        { name: 'Analyst Partner', role: 'profiled the dataset schema and risk fields', status: 'complete' },
        { name: 'Processor Partner', role: 'counted firms and features in the source', status: 'complete' },
        { name: 'Executive Partner', role: 'framed safe-use guidance', status: 'complete' },
      ],
      confidence: 92,
      evidence: stats ? [`${firms} synthetic firms (exact row count)`, `${feats} feature columns: ${colList}`] : ['Exact counts computed from the source file'],
      recommendations: ['Use only for prototyping / demos', 'Treat as synthetic — never use as real customer data', 'Load sample into the credit model sandbox'],
      routedTo: 'Analyst Partner',
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
        { name: 'Analyst Partner', role: 'Automated Spreading + financial analysis and scoring', status: 'complete' },
        { name: 'Risk Assessment Agent', role: 're-validated exposure and conditions', status: 'complete' },
      ],
      confidence: 88,
      evidence: ['DSCR 1.62× above 1.2× policy floor', 'PD 2.8% vs portfolio average 2.6%', 'Leverage 2.9× within sector norm'],
      recommendations: ['Approve $2.5M with conditions', 'Require personal guarantee', 'Set quarterly covenant reporting'],
      routedTo: 'Analyst Partner',
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
        { name: 'Processor Partner', role: 'routed escalation and workflow', status: 'complete' },
        { name: 'Compliance (AML) Agent', role: 'ran typology detection and risk scoring', status: 'complete' },
      ],
      confidence: 91,
      evidence: ['$1.2M moved in rapid-fire transfers', '3 counterparties in high-risk jurisdictions', 'Customer profile inconsistent with cash/transfer volume'],
      recommendations: ['Escalate to full compliance review', 'File SAR on the account', 'Freeze the account pending investigation'],
      routedTo: 'Processor Partner',
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
        { name: 'Risk Assessment Agent', role: 'ran scenario and capital projection', status: 'complete' },
        { name: 'CFO Advisor', role: 'translated into capital-planning recommendation', status: 'complete' },
      ],
      confidence: 82,
      evidence: ['CRE stress drives $110M expected loss', 'CET1 breaches the 10.5% floor', 'LCR headroom narrows 22pp'],
      recommendations: ['Increase CRE loan-loss provisions (~$18M)', 'Raise additional Tier 1 capital', 'Reduce CRE concentration'],
      routedTo: 'Executive Partner',
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
      { name: 'Service Partner', role: 'synthesized the response', status: 'complete' },
    ],
    confidence: 70,
    evidence: ['Response framed from current module context'],
    recommendations: ['Narrow the question to a specific client, case, or scenario'],
    routedTo: 'Service Partner',
    humanApprovalNeeded: false,
  };
}

app.listen(port, () => {
  console.log(`BankRisk backend running on http://localhost:${port}`);
  console.log(openai ? `AI connected (${model})` : 'AI OFF — no OPENAI_API_KEY set. Using mock responses.');
});