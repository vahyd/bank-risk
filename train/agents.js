/* BankRisk — train the per-section AI agents on the Zenodo synthetic firm dataset.
   Fits a linear credit-risk model on the dataset's hazard score (the intended risk
   target) and derives data-driven knowledge for every module. Artifacts are
   persisted to data/trained/agents.json and ground every section's agent. */
'use strict';

const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, '..', 'data', 'firms_features_clean.csv');
const OUT_FILE = path.join(__dirname, '..', 'data', 'trained', 'agents.json');

const LGD = 0.45;
const PORTFOLIO_USD_M = 2400;
const GRADES = [
  { max: 0.02, grade: 'A', tone: 'green' },
  { max: 0.04, grade: 'A-', tone: 'green' },
  { max: 0.06, grade: 'B+', tone: 'green' },
  { max: 0.10, grade: 'B', tone: 'amber' },
  { max: 0.16, grade: 'B-', tone: 'amber' },
  { max: 0.25, grade: 'CCC', tone: 'red' },
  { max: 1.01, grade: 'D', tone: 'red' },
];
const SECTOR_CROSSSELL = {
  Manufacturing: ['Working Capital Facility', 'Equipment Financing', 'Trade Finance'],
  Services: ['Cash Management', 'FX Hedging', 'Revolving Credit'],
  Technology: ['Venture Debt', 'FX Hedging', 'Liquidity Sweep'],
  Retail: ['Inventory Financing', 'Merchant Services', 'Receivables Financing'],
  Finance: ['Repo / Collateral Lines', 'Liquidity Sweep', 'Counterparty Lines'],
  Energy: ['Commodity Hedging', 'Project Finance', 'FX Hedging'],
};
const SECTOR_STRESS = {
  recession: { Services: 1.92, Technology: 1.73, Manufacturing: 1.73, Retail: 2.50, Finance: 2.11, Energy: 1.92 },
  housing: { Services: 1.68, Technology: 1.44, Manufacturing: 1.68, Retail: 2.64, Finance: 3.12, Energy: 1.56 },
  rate: { Services: 3.12, Technology: 2.62, Manufacturing: 2.79, Retail: 2.62, Finance: 3.61, Energy: 2.95 },
  currency: { Services: 1.84, Technology: 1.73, Manufacturing: 2.07, Retail: 1.96, Finance: 1.61, Energy: 2.19 },
  cre: { Services: 3.60, Technology: 2.64, Manufacturing: 3.12, Retail: 5.76, Finance: 4.80, Energy: 2.88 },
};
const CAPITAL_SENSITIVITY = 30;

/* ---------- deterministic RNG + math ---------- */
function mulberry32(seed) {
  let a = seed;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ---------- CSV parsing (EU decimal commas, quotes, BOM) ---------- */
function normalizeCell(v) {
  const s = String(v).trim();
  if (s === '') return '';
  if (/^[-+]?\d+,\d+$/.test(s)) { const n = Number(s.replace(',', '.')); if (Number.isFinite(n)) return n; }
  if (/^[-+]?\d*\.?\d+$/.test(s)) { const n = Number(s); if (Number.isFinite(n)) return n; }
  return s;
}

function parseCSVLine(line) {
  const out = [];
  let cur = '', inQ = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (inQ) {
      if (c === '"') { if (line[i + 1] === '"') { cur += '"'; i++; } else inQ = false; }
      else cur += c;
    } else if (c === '"') inQ = true;
    else if (c === ',') { out.push(cur); cur = ''; }
    else cur += c;
  }
  out.push(cur);
  return out.map(normalizeCell);
}

/* ---------- load ---------- */
function loadRows() {
  const text = fs.readFileSync(DATA_FILE, 'utf8').replace(/^\uFEFF/, '');
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== '');
  const header = parseCSVLine(lines[0]);
  const idx = {};
  header.forEach((c, i) => { if (c && !/^Unnamed/i.test(c)) idx[c] = i; });
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const c = parseCSVLine(lines[i]);
    if (!c[idx.Firm_ID]) continue;
    const status = Number(c[idx.Status]) || 0;
    const leverage = Number(c[idx.Leverage]) || 0;
    if (!leverage && !status) continue;
    rows.push({
      firmId: String(c[idx.Firm_ID]),
      sector: String(c[idx.Sector]),
      region: String(c[idx.Region]),
      size: Number(c[idx.Size]) || 0,
      leverage,
      margin: Number(c[idx.Profit_Margin]) || 0,
      rd: Number(c[idx.RD_Intensity]) || 0,
      complexity: Number(c[idx.Org_Complexity]) || 0,
      baseHazard: Number(c[idx.base_hazard]) || 0,
      covEffect: Number(c[idx.cov_effect]) || 0,
      hazard: Number(c[idx.hazard]) || 0,
      eventTime: Number(c[idx.Event_Time]) || 0,
      status,
    });
  }
  return rows;
}

const SECTORS = ['Services', 'Technology', 'Manufacturing', 'Retail', 'Finance', 'Energy'];
const REGIONS = ['USA', 'LatAm', 'Europe'];
const D = 5 + (SECTORS.length - 1) + (REGIONS.length - 1);

function features(r, mean, sd) {
  const z = (v, i) => (v - mean[i]) / sd[i];
  const f = [
    z(Math.log(r.size + 1), 0), z(r.leverage, 1), z(r.margin, 2), z(r.rd, 3), z(r.complexity, 4),
  ];
  SECTORS.slice(1).forEach((s) => f.push(r.sector === s ? 1 : 0));
  REGIONS.slice(1).forEach((reg) => f.push(r.region === reg ? 1 : 0));
  return f;
}

/* ---------- ridge regression (SGD) on the dataset's hazard score ---------- */
function fitModel(train) {
  const n = train.length;
  const mean = [0, 0, 0, 0, 0];
  const sd = [1, 1, 1, 1, 1];
  const logSizes = train.map((r) => Math.log(r.size + 1));
  const comps = [logSizes, train.map((r) => r.leverage), train.map((r) => r.margin), train.map((r) => r.rd), train.map((r) => r.complexity)];
  comps.forEach((arr, i) => {
    mean[i] = arr.reduce((a, b) => a + b, 0) / n;
    sd[i] = Math.sqrt(arr.reduce((a, b) => a + (b - mean[i]) * (b - mean[i]), 0) / n) || 1;
  });
  const X = train.map((r) => features(r, mean, sd));
  const y = train.map((r) => r.hazard);
  const w = new Float64Array(D);
  let b = 0;
  const lr = 0.12, epochs = 28, lambda = 0.004, batch = 256;
  for (let e = 0; e < epochs; e++) {
    for (let start = 0; start < n; start += batch) {
      const end = Math.min(start + batch, n);
      let gb = 0;
      const gw = new Float64Array(D);
      for (let i = start; i < end; i++) {
        const pred = b + X[i].reduce((a, v, k) => a + w[k] * v, 0);
        const err = pred - y[i];
        for (let k = 0; k < D; k++) gw[k] += err * X[i][k];
        gb += err;
      }
      const m = end - start;
      for (let k = 0; k < D; k++) w[k] -= lr * (gw[k] / m + lambda * w[k]);
      b -= lr * (gb / m);
    }
  }
  const predict = (r) => {
    const Xr = features(r, mean, sd);
    return Math.min(0.99, Math.max(0.002, b + Xr.reduce((a, v, k) => a + w[k] * v, 0)));
  };
  return { coef: { w: Array.from(w), b, mean, sd, D }, predict };
}

/* ---------- metrics ---------- */
function r2Pearson(y, p) {
  const my = y.reduce((a, b) => a + b, 0) / y.length;
  const mp = p.reduce((a, b) => a + b, 0) / p.length;
  const ssTot = y.reduce((a, v) => a + (v - my) * (v - my), 0);
  const ssRes = y.reduce((a, v, i) => a + (p[i] - v) * (p[i] - v), 0);
  const r2 = 1 - ssRes / ssTot;
  const cov = y.reduce((a, v, i) => a + (p[i] - mp) * (v - my), 0);
  const corr = cov / (Math.sqrt(p.reduce((a, v) => a + (v - mp) * (v - mp), 0)) * Math.sqrt(ssTot)) || 0;
  return { r2, corr };
}

function gradeOf(risk) {
  for (const g of GRADES) if (risk < g.max) return g;
  return GRADES[GRADES.length - 1];
}
const scoreOf = (r) => Math.max(5, Math.round(95 - (r - 0.005) * 420));
const pct1 = (v) => (v * 100).toFixed(1) + '%';

/* ---------- per-section knowledge derivation ---------- */
function trainSections(rows, model, totals) {
  const scaleEad = PORTFOLIO_USD_M / totals.size;
  const firmEad = (r) => r.size * scaleEad;

  const seg = {};
  const seedSeg = (k) => { if (!seg[k]) seg[k] = { firms: 0, ead: 0, defaults: 0, margin: 0, lev: 0, risk: 0 }; };

  const predicted = rows.map((r) => {
    const risk = model.predict(r);
    return { r, risk };
  });

  predicted.forEach(({ r, risk }) => {
    seedSeg('s:' + r.sector); seedSeg('r:' + r.region);
    const s = seg['s:' + r.sector]; s.firms++; s.ead += firmEad(r); s.defaults += r.status; s.margin += r.margin; s.lev += r.leverage; s.risk += risk;
    const rg = seg['r:' + r.region]; rg.firms++; rg.ead += firmEad(r); rg.defaults += r.status; rg.margin += r.margin; rg.lev += r.leverage; rg.risk += risk;
  });
  const fin = (k) => { const a = seg[k]; return { firms: a.firms, ead: a.ead, defaultRate: a.defaults / a.firms, meanPD: a.risk / a.firms, meanMargin: a.margin / a.firms, meanLeverage: a.lev / a.firms }; };

  const sectorStats = SECTORS.map((s) => ({ sector: s, ...fin('s:' + s) })).sort((a, b) => b.meanPD - a.meanPD);
  const regionStats = REGIONS.map((reg) => ({ region: reg, ...fin('r:' + reg) }));

  const ranked = predicted.slice().sort((a, b) => b.risk - a.risk);
  const drivers = (r, risk) => {
    const d = [];
    if (r.leverage > 0.7) d.push('Leverage ' + (r.leverage * 100).toFixed(0) + '%');
    if (r.margin < 0) d.push('Negative margin ' + (r.margin * 100).toFixed(1) + '%');
    if (r.complexity > 5) d.push('Org complexity ' + r.complexity);
    if (r.rd > 1.2) d.push('High R&D intensity');
    if (risk > 0.2) d.push('Model PD ' + (risk * 100).toFixed(1) + '%');
    return d.slice(0, 3);
  };

  const watchlist = ranked.slice(0, 25).map(({ r, risk }) => ({
    firm: 'Firm ' + r.firmId, sector: r.sector, region: r.region, pd: +(risk * 100).toFixed(1),
    riskScore: Math.round(Math.min(100, risk * 260)), distress: Math.round(Math.min(100, risk * 190)),
    severity: risk > 0.12 ? 'High' : risk > 0.06 ? 'Medium' : 'Low',
    drivers: drivers(r, risk),
  }));

  const rankedAsc = predicted.slice().sort((a, b) => a.risk - b.risk);
  const appFractions = [0.06, 0.24, 0.42, 0.6, 0.76, 0.92];
  const applications = appFractions.map((f, i) => {
    const { r, risk } = rankedAsc[Math.floor(f * (rankedAsc.length - 1))];
    const g = gradeOf(risk);
    const requested = Math.round(firmEad(r) * (i % 2 ? 0.8 : 1.3) * 10) / 10;
    const rec = risk < 0.04 ? 'Approve' : risk < 0.09 ? 'Approve with conditions' : 'Decline';
    return {
      id: 'APP-' + String(2010 + i),
      name: `${r.sector} Group ${r.firmId.slice(-3)}`,
      industry: r.sector, region: r.region,
      requested, score: scoreOf(risk), pd: +(risk * 100).toFixed(1), grade: g.grade,
      recTone: g.tone, confidence: Math.round(84 + (0.1 - risk) * 40),
      inputs: ['Synthetic financial statements', '2 years tax returns'],
      metrics: [['Leverage (Debt/Assets)', (r.leverage * 100).toFixed(1) + '%'], ['Profit margin', (r.margin * 100).toFixed(1) + '%'], ['R&D intensity', r.rd.toFixed(2)], ['Org complexity', String(r.complexity)], ['Model PD', (risk * 100).toFixed(1) + '%']],
      memo: `${r.sector} firm, ${r.region}, model PD ${(risk * 100).toFixed(1)}%. ${r.leverage > 0.6 ? 'High leverage relative to sector.' : 'Leverage within sector norm.'} ${r.margin < 0 ? 'Margins are negative.' : 'Margins are positive.'} Recommendation: ${rec}.`,
      recommendation: rec,
    };
  });

  const clients = predicted.slice().sort((a, b) => b.r.size - a.r.size).slice(0, 6)
    .map(({ r, risk }, i) => {
      const ead = firmEad(r);
      const health = Math.round(Math.max(5, Math.min(99, (0.86 - risk * 1.9 - (r.leverage > 0.6 ? 0.06 : 0) + (r.margin > 0 ? 0.06 : -0.04)) * 100)));
      return {
        name: `${r.sector} Group ${String.fromCharCode(65 + i)}`,
        industry: r.sector, region: r.region,
        deposits: Math.round(ead * 0.55 * 10) / 10, loans: Math.round(ead * 1.25 * 10) / 10,
        profitability: Math.round((0.4 + r.margin) * 100) / 100,
        riskLabel: risk < 0.05 ? 'Low' : risk < 0.1 ? 'Medium' : 'High',
        products: ['Loan', 'Deposit Account'],
        suggestions: SECTOR_CROSSSELL[r.sector].map((p, j) => ({ p, r: 6 + Math.round((11 - risk * 30 + j * 2 + i * 1.3) % 14) })),
        brief: `${r.sector} firm, ${r.region}. Model PD ${(risk * 100).toFixed(1)}%. ${r.margin < 0 ? 'Margin pressure — review facility pricing.' : 'Healthy margins; good cross-sell candidates.'}`,
        alerts: risk > 0.1 ? ['Model PD above 10%', 'Review credit facility pricing'] : risk > 0.06 ? ['Elevated model risk'] : ['No issues'],
        pd: +(risk * 100).toFixed(1),
      };
    });

  const ecl = predicted.reduce((a, { r, risk }) => a + firmEad(r) * risk * LGD, 0);
  const scenarios = [
    { id: 'recession', name: 'Recession', shock: 'GDP −3%' },
    { id: 'housing', name: 'Housing Crash', shock: 'House prices −25%' },
    { id: 'rate', name: 'Rate Hike', shock: 'Rates +300bp' },
    { id: 'currency', name: 'Currency Crisis', shock: 'FX −30%' },
    { id: 'cre', name: 'CRE Downturn', shock: 'Commercial RE −20%' },
  ].map((sc) => {
    const m = SECTOR_STRESS[sc.id];
    const loss = predicted.reduce((a, { r, risk }) => {
      const spd = Math.min(0.99, risk * (m[r.sector] || 1.5));
      return a + firmEad(r) * spd * LGD;
    }, 0);
    const delta = (loss - ecl) / CAPITAL_SENSITIVITY;
    const after = +(14.2 - delta).toFixed(1);
    return { ...sc, loss: Math.round(loss), uplift: Math.round(loss - ecl), after, breach: after < 10.5 };
  });

  const amlRows = predicted.slice().sort((a, b) => b.r.hazard - a.r.hazard || b.r.complexity - a.r.complexity)
    .filter(({ r }) => r.covEffect > 3).slice(0, 8)
    .map(({ r, risk }, i) => ({
      alert: i % 2 === 0 ? 'Rapid turnover in cash' : 'Unusual transfer pattern',
      customer: `${r.sector} Trucks ${String.fromCharCode(65 + i)}`,
      risk: risk > 0.16 || r.covEffect > 5 ? 'High' : 'Medium',
      amount: i % 3 === 0 ? '—' : `$${Math.round(firmEad(r) * 0.15)}K`,
      rec: risk > 0.16 ? 'Escalate to compliance review' : 'Enhanced due diligence',
      note: `${r.sector} firm, ${r.region}. Covariate effect ${r.covEffect.toFixed(2)} and model PD ${(risk * 100).toFixed(1)}% sit in the riskiest decile of the trained portfolio.`,
    }));

  const focus = ecl * 1.6;
  const treasury = {
    gap: Math.round(focus), date: 'Q2 2028',
    recommendation: focus > 90 ? 'Issue 5-year bond' : 'Issue 3-year bond',
    lcr: Math.round(128 - Math.min(12, ecl * 0.1)), nsfr: Math.round(112 - Math.min(10, ecl * 0.08)),
    forecast: [40, 32, 22, 8, -14, -42, -78, -120].map((v) => Math.round(v * (0.85 + Math.min(0.45, focus / 160)))),
  };

  const concentration = sectorStats.map((s) => ({ sector: s.sector, share: Math.round(s.ead / totals.eadx * 100) }));

  return {
    underwriting: { model: 'ridge regression on hazard (SRD, L2)', applications, gradeRules: GRADES.map((g) => `${g.grade} < ${(g.max * 100).toFixed(1)}%`), ecl, lgd: LGD },
    earlyWarning: { model: 'predicted hazard + covariate ranking', watchlist, thresholds: { High: 'PD > 12%', Medium: 'PD 6–12%', Low: 'PD < 6%' } },
    rmCopilot: { model: 'client-book derivation (size × risk → relationship health)', clients, crossSellRules: SECTOR_CROSSSELL },
    portfolioRisk: { model: 'segment exposure × trained PD', sectorStats, regionStats, ecl, concentration },
    stressTesting: { model: 'sector-scaled PD uplifts → ECL → CET1', scenarios, lgd: LGD },
    cfoAI: {
      model: 'ECL / capital planning on trained portfolio',
      ecl, eadM: totals.eadx, cet1: 14.2, lgd: LGD,
      recommendations: scenarios.filter((s) => s.breach).map((s) => ({ scenario: s.name, action: 'Raise Tier 1 + increase provisions', reason: `${s.name} drops CET1 to ${s.after}% (floor 10.5%)` }))
        .concat([{ scenario: 'baseline', action: 'Maintain provisioning', reason: `Baseline ECL $${ecl.toFixed(0)}M on $${Math.round(totals.eadx)}M EAD` }]),
    },
    aml: { model: 'hazard/covariate outlier scoring', rules: ['cov_effect > 3 flagged', 'org complexity in top decile', 'hazard in top decile'], alerts: amlRows },
    treasury: { model: 'portfolio ECL → liquidity gap', ...treasury },
    datasetAgent: { model: 'exact-count schema profiler', stats: { firms: rows.length, features: 13 }, defaultRate: totals.defaults / totals.firms },
    overview: { model: 'portfolio aggregation', firms: rows.length, defaultRate: totals.defaults / totals.firms, eadM: Math.round(totals.eadx), ecl, bySectorSummary: sectorStats.slice(0, 3), byRegionSummary: regionStats.slice(0, 3) },
    digitalPartners: { model: 'intent-router (unchanged), grounded on trained artifacts', roster: ['Executive Partner', 'Analyst Partner', 'Service Partner', 'Processor Partner', 'Client Partner'] },
  };
}

/* ---------- master train ---------- */
async function train() {
  const rows = loadRows();
  const totals = {
    firms: rows.length,
    defaults: rows.reduce((a, r) => a + r.status, 0),
    size: rows.reduce((a, r) => a + r.size, 0),
  };
  totals.eadx = totals.size * (PORTFOLIO_USD_M / totals.size);

  const rng = mulberry32(7);
  const shuffled = rows.slice().sort(() => rng() - 0.5);
  const split = Math.floor(shuffled.length * 0.8);
  const trainRows = shuffled.slice(0, split);
  const testRows = shuffled.slice(split);

  const model = fitModel(trainRows);
  const y = testRows.map((r) => r.hazard);
  const p = testRows.map(model.predict);
  const { r2, corr } = r2Pearson(y, p);

  const sections = trainSections(rows, model, totals);
  const artifact = {
    trainedAt: new Date().toISOString(),
    dataset: { recordId: '18115815', file: 'firms_features_clean.csv', firms: rows.length, features: 13, defaultRate: +(totals.defaults / totals.firms).toFixed(4) },
    model: { type: 'ridge-regression (SGD, L2) on dataset hazard', features: ['log(Size)', 'Leverage', 'Profit_Margin', 'RD_Intensity', 'Org_Complexity', 'Sector dummies', 'Region dummies'], r2: +r2.toFixed(4), corr: +corr.toFixed(4), trainedOn: split, evaluatedOn: testRows.length, grades: GRADES.map((g) => `${g.grade} < ${(g.max * 100).toFixed(1)}%`) },
    sections,
  };
  fs.mkdirSync(path.dirname(OUT_FILE), { recursive: true });
  fs.writeFileSync(OUT_FILE, JSON.stringify(artifact, null, 2));
  console.log(`[train] ${rows.length} firms · R2 ${r2.toFixed(3)} corr ${corr.toFixed(3)} → ${OUT_FILE}`);
  return artifact;
}

let cached = null;

function load() {
  if (cached) return cached;
  try { cached = JSON.parse(fs.readFileSync(OUT_FILE, 'utf8')); } catch (e) { cached = null; }
  return cached;
}

function summary() {
  const a = load();
  if (!a) return null;
  return { trainedAt: a.trainedAt, dataset: a.dataset, model: a.model, sections: Object.keys(a.sections) };
}

module.exports = { train, load, summary, OUT_FILE, DATA_FILE };