/* BankRisk — AI Banking Operating System (vanilla JS demo). */
'use strict';
(function () {
  const el = document.querySelector('#view');
  const money = (m) => { const s = m < 0 ? '-' : ''; const a = Math.abs(m); return a >= 1000 ? s + '$' + (a / 1000).toFixed(1) + 'B' : s + '$' + a.toFixed(1) + 'M'; };

  /* ---------- mock data ---------- */
  const kpis = [
    { label: 'Active clients', value: '1,248', sub: 'Commercial + SME' },
    { label: 'Loan portfolio', value: '$2.4B', sub: 'Across 14 sectors' },
    { label: 'Weighted PD', value: '2.6%', sub: 'Portfolio default prob.' },
    { label: 'Capital ratio', value: '14.2%', sub: 'CET1 · above 10.5% min' },
    { label: 'Watchlist clients', value: '37', sub: 'Elevated risk' },
    { label: 'Open AML alerts', value: '12', sub: '5 high priority' },
  ];
  const lifecycle = ['Prospect', 'Relationship Manager', 'Credit Underwriting', 'Loan Approval', 'Portfolio Monitoring', 'Treasury Management', 'Enterprise Risk Management'];
  const ranking = [
    { name: 'Credit Underwriting Agent', stars: 5 },
    { name: 'Early Warning System', stars: 5 },
    { name: 'Relationship Manager Copilot', stars: 5 },
    { name: 'Treasury & Liquidity Copilot', stars: 4 },
    { name: 'Portfolio Risk Simulator', stars: 4 },
    { name: 'AML Investigation Agent', stars: 4 },
  ];

  const clients = [
    { name: 'ABC Manufacturing', industry: 'Manufacturing', deposits: 8.4, loans: 12.5, profitability: 0.42, riskLabel: 'Low',
      products: ['Loan', 'Deposit Account'],
      suggestions: [{ p: 'FX Hedging', r: 18 }, { p: 'Cash Management', r: 14 }, { p: 'Working Capital Facility', r: 10 }],
      brief: 'Strong Q3 results. CFO planning expansion into two new markets; candidate for a working-capital facility and FX hedging to cover imported inputs.',
      alerts: ['Deposit balance stable', 'No missed repayments'] },
    { name: 'Delta Foods Co.', industry: 'Food & Beverage', deposits: 5.1, loans: 9.8, profitability: 0.28, riskLabel: 'Low',
      products: ['Deposit Account'],
      suggestions: [{ p: 'Term Loan', r: 22 }, { p: 'Cash Management', r: 9 }, { p: 'Trade Finance', r: 12 }],
      brief: 'Seasonal working-capital needs ahead of Q4 demand. Introduced treasury contact.',
      alerts: ['Deposit balance stable'] },
    { name: 'Gamma Retail Group', industry: 'Retail', deposits: 3.2, loans: 15.4, profitability: 0.11, riskLabel: 'Medium',
      products: ['Loan', 'Deposit Account', 'Merchant Services'],
      suggestions: [{ p: 'Inventory Financing', r: 16 }, { p: 'FX Hedging', r: 7 }],
      brief: 'Margin pressure noted; review pricing of credit facilities. Cross-sell inventory financing.',
      alerts: ['Overdraft usage rising'] },
    { name: 'Zeta Pharmaceuticals', industry: 'Healthcare', deposits: 12.8, loans: 6.2, profitability: 0.55, riskLabel: 'Low',
      products: ['Deposit Account', 'Loan'],
      suggestions: [{ p: 'Cash Management', r: 11 }, { p: 'FX Hedging', r: 15 }, { p: 'Liquidity Sweep', r: 8 }],
      brief: 'High cash balances underutilized. Propose liquidity sweep and FX hedging.',
      alerts: ['No issues'] },
    { name: 'Epsilon Logistics', industry: 'Logistics', deposits: 2.4, loans: 18.9, profitability: 0.06, riskLabel: 'High',
      products: ['Loan'],
      suggestions: [{ p: 'Working Capital Facility', r: 20 }, { p: 'Receivables Financing', r: 14 }],
      brief: 'Leverage elevated; consider restructuring and receivables financing.',
      alerts: ['Missed repayment last cycle', 'Falling deposits'] },
  ];

  const applications = [
    { id: 'APP-1042', name: 'Delta Foods Co.', industry: 'Food & Beverage', requested: 2.5, score: 74, pd: 2.8, grade: 'B+', recommendation: 'Approve with conditions', recTone: 'green', confidence: 88,
      inputs: ['FY2023 financial statements', '2 years tax returns', '12 months bank statements'],
      metrics: [['Revenue growth (YoY)', '+11.4%'], ['Debt service coverage', '1.62×'], ['Current ratio', '1.38×'], ['Leverage (Debt/EBITDA)', '2.9×'], ['Gross margin', '24.1%']],
      memo: 'Consistent revenue growth and adequate debt-service coverage. Moderate leverage is offset by a diversified customer base. Recommend approval subject to a personal guarantee and quarterly covenant reporting.' },
    { id: 'APP-1043', name: 'Helios Hospitality', industry: 'Hospitality', requested: 4.8, score: 58, pd: 6.9, grade: 'B-', recommendation: 'Approve with conditions', recTone: 'amber', confidence: 71,
      inputs: ['FY2023 financial statements', '2 years tax returns', '12 months bank statements'],
      metrics: [['Revenue growth (YoY)', '−2.1%'], ['Debt service coverage', '1.12×'], ['Current ratio', '0.94×'], ['Leverage (Debt/EBITDA)', '4.6×'], ['Gross margin', '38.0%']],
      memo: 'Thin debt-service coverage and negative revenue growth. Strong asset quality partially offsets. Recommend approval with higher pricing and a 24-month amortization schedule.' },
    { id: 'APP-1044', name: 'Nova Logistics', industry: 'Logistics', requested: 1.9, score: 81, pd: 1.4, grade: 'A-', recommendation: 'Approve', recTone: 'green', confidence: 94,
      inputs: ['FY2023 financial statements', '2 years tax returns', '12 months bank statements'],
      metrics: [['Revenue growth (YoY)', '+18.6%'], ['Debt service coverage', '2.41×'], ['Current ratio', '1.72×'], ['Leverage (Debt/EBITDA)', '1.8×'], ['Gross margin', '19.4%']],
      memo: 'Strong growth, low leverage, and comfortable coverage. Clean repayment history. Recommend standard approval.' },
    { id: 'APP-1045', name: 'Vertex Retail', industry: 'Retail', requested: 3.2, score: 43, pd: 12.5, grade: 'CCC', recommendation: 'Decline', recTone: 'red', confidence: 90,
      inputs: ['FY2023 financial statements', '1 year tax returns', '6 months bank statements'],
      metrics: [['Revenue growth (YoY)', '−14.8%'], ['Debt service coverage', '0.71×'], ['Current ratio', '0.62×'], ['Leverage (Debt/EBITDA)', '7.8×'], ['Gross margin', '16.2%']],
      memo: 'Negative growth, coverage below 1.0×, and high leverage indicate elevated default risk. Recommend decline.' },
    { id: 'APP-1046', name: 'Aurora Manufacturing', industry: 'Manufacturing', requested: 6.0, score: 66, pd: 4.3, grade: 'B', recommendation: 'Approve with conditions', recTone: 'amber', confidence: 80,
      inputs: ['FY2023 financial statements', '2 years tax returns', '12 months bank statements'],
      metrics: [['Revenue growth (YoY)', '+5.9%'], ['Debt service coverage', '1.35×'], ['Current ratio', '1.21×'], ['Leverage (Debt/EBITDA)', '3.5×'], ['Gross margin', '27.6%']],
      memo: 'Adequate profile with stable cash flows. Larger ticket size warrants a syndication or shared collateral. Approve with additional collateral requirements.' },
  ];

  const watchlist = [
    { client: 'Zeta Retail', sector: 'Retail', risk: 81, distress: 67, drivers: ['Revenue decline', 'Increased overdraft usage', 'Falling deposits'], severity: 'High' },
    { client: 'Omega Textiles', sector: 'Manufacturing', risk: 72, distress: 54, drivers: ['Margin compression', 'Rising inventory days'], severity: 'High' },
    { client: 'Lambda Hospitality', sector: 'Hospitality', risk: 58, distress: 38, drivers: ['Seasonal cash-flow gap'], severity: 'Medium' },
    { client: 'Sigma Construction', sector: 'Construction', risk: 44, distress: 22, drivers: ['Delayed receivables'], severity: 'Medium' },
    { client: 'Phi Logistics', sector: 'Logistics', risk: 22, distress: 9, drivers: ['Stable'], severity: 'Low' },
  ];

  const scenarios = [
    { id: 'recession', name: 'Recession', shock: 'GDP −3.0%', loss: 62, before: 14.2, after: 12.4 },
    { id: 'housing', name: 'Housing Crash', shock: 'House prices −25%', loss: 78, before: 14.2, after: 11.7 },
    { id: 'rate', name: 'Rate Hike', shock: 'Interest rates +3.0%', loss: 95, before: 14.2, after: 11.1 },
    { id: 'currency', name: 'Currency Crisis', shock: 'FX depreciation −30%', loss: 41, before: 14.2, after: 13.0 },
    { id: 'cre', name: 'CRE Downturn', shock: 'Commercial RE −20%', loss: 110, before: 14.2, after: 10.4 },
  ];

  const alerts = [
    { alert: 'Unusual international transfers', customer: 'Omega Trading Ltd', risk: 'High', amount: '$1.2M', rec: 'Escalate to compliance review', note: 'Rapid-fire transfers to high-risk jurisdictions over five days.' },
    { alert: 'Structuring / smurfing pattern', customer: 'Beta Holdings', risk: 'High', amount: '$480K', rec: 'File SAR and freeze account', note: 'Multiple deposits just below the reporting threshold.' },
    { alert: 'Rapid turnover in cash', customer: 'Gamma Retail', risk: 'Medium', amount: '$210K', rec: 'Enhanced due diligence', note: 'Cash-intensive activity inconsistent with customer profile.' },
    { alert: 'PEP linkage detected', customer: 'Alpha Ventures', risk: 'Medium', amount: '—', rec: 'Monitor and re-score', note: 'New connection to a politically exposed person.' },
    { alert: 'Sanctioned-entity match', customer: 'Delta Imports', risk: 'High', amount: '$90K', rec: 'Block and escalate', note: 'Name matches a sanctions list (90% confidence).' },
  ];

  const treasury = {
    gap: 120, date: 'Q2 2028', recommendation: 'Issue 5-year bond',
    forecast: [{ m: 'M1', v: 40 }, { m: 'M2', v: 32 }, { m: 'M3', v: 22 }, { m: 'M4', v: 8 }, { m: 'M5', v: -14 }, { m: 'M6', v: -42 }, { m: 'M7', v: -78 }, { m: 'M8', v: -120 }],
  };

  const stressScenarios = [
    { id: 'recession', name: 'Recession', shock: 'GDP −3%', loss: 62, revenue: -18, capitalDelta: 1.8, lcrDelta: 14 },
    { id: 'rate', name: 'Rate Hike', shock: 'Rates +300bp', loss: 95, revenue: -24, capitalDelta: 3.1, lcrDelta: 10 },
    { id: 'housing', name: 'Housing Crash', shock: 'HPI −25%', loss: 78, revenue: -15, capitalDelta: 2.5, lcrDelta: 16 },
    { id: 'currency', name: 'Currency Crisis', shock: 'FX −30%', loss: 41, revenue: -9, capitalDelta: 1.2, lcrDelta: 6 },
    { id: 'cre', name: 'CRE Downturn', shock: 'CRE −20%', loss: 110, revenue: -12, capitalDelta: 3.8, lcrDelta: 22 },
  ];
  const severities = [
    { id: 'baseline', name: 'Baseline', mult: 0 },
    { id: 'adverse', name: 'Adverse', mult: 1.0 },
    { id: 'severe', name: 'Severely Adverse', mult: 1.6 },
  ];
  const cfoRecs = [
    { advisor: 'Treasury Advisor', action: 'Issue 5-year bond', confidence: 85, reason: 'Funding gap of $120M projected by Q2 2028; lock current rates.', impact: 'Saves ~$2.1M/yr vs floating' },
    { advisor: 'Risk Manager', action: 'Increase CRE loan-loss provisions', confidence: 72, reason: 'CRE stress test drives capital below the 10.5% buffer.', impact: 'Reduces expected loss by $18M' },
    { advisor: 'CFO Advisor', action: 'Refinance short-term debt', confidence: 78, reason: 'Rate outlook is rising; extend maturities now.', impact: 'Lowers interest-rate risk' },
    { advisor: 'Risk Manager', action: 'Reduce retail-sector concentration', confidence: 68, reason: 'Retail default rates trend above portfolio average.', impact: 'Lowers concentration risk' },
    { advisor: 'Treasury Advisor', action: 'Deploy excess liquidity into HQLA', confidence: 81, reason: 'LCR headroom supports higher-yield liquid assets.', impact: '+$1.4M/yr yield' },
    { advisor: 'CFO Advisor', action: 'Raise additional Tier 1 capital', confidence: 64, reason: 'Severe stress consumes capital buffers.', impact: 'Restores 1.2% CET1 headroom' },
  ];

  /* ---------- state ---------- */
  const state = { page: 'Overview', client: 0, app: 0, severity: 'All', scenario: 2, alert: 0, stressScenario: 2, stressSeverity: 1, partner: null };

  /* ---------- helpers ---------- */
  const title = (name, desc, tag) => `<div class="title"><div><span>BANKRISK · ${state.page.toUpperCase()}</span><h1>${name}</h1><p>${desc}</p></div><i class="status">● ${tag}</i></div>`;
  const kpi = (l, v, s, tone = '') => `<div class="kpi"><label>${l}</label><b class="${tone}">${v}</b><small>${s}</small></div>`;
  const chip = (tone, text) => `<span class="chip ${tone}">${text}</span>`;

  /* ---------- pages ---------- */
  function overview() {
    el.innerHTML = title('Executive overview', 'An AI-powered operating system across the commercial lending lifecycle.', 'PRODUCTION') +
      `<div class="kpis">${kpis.map((k) => kpi(k.label, k.value, k.sub)).join('')}</div>` +
      `<div class="card"><h2>Lending lifecycle</h2><p class="sub">Every stage, augmented by an AI module</p>
        <div class="flow">${lifecycle.map((s, i) => `<span class="step">${s}</span>${i < lifecycle.length - 1 ? '<span class="arrow">→</span>' : ''}`).join('')}</div></div>` +
      `<div class="grid" style="margin-top:16px">
        <div class="card"><h2>Module ranking</h2><p class="sub">By business impact</p>
          <table><thead><tr><th>#</th><th>Module</th><th>Impact</th></tr></thead><tbody>
          ${ranking.map((r, i) => `<tr><td><b>${i + 1}</b></td><td>${r.name}</td><td class="stars">${'★'.repeat(r.stars)}${'☆'.repeat(5 - r.stars)}</td></tr>`).join('')}
          </tbody></table></div>
        <div class="card"><h2>Platform vision</h2><p class="sub">Each module drives revenue or reduces loss</p>
          ${[['Relationship Manager Copilot', 'Grow revenue'], ['Credit Underwriting Agent', 'Improve lending quality'], ['Early Warning System', 'Reduce defaults'], ['Treasury Copilot', 'Manage liquidity'], ['Portfolio Simulator', 'Manage enterprise risk'], ['AML Agent', 'Reduce compliance risk']].map((x) => `<div class="prod"><span>${x[0]}</span><b>${x[1]}</b></div>`).join('')}</div>
      </div>`;
  }

  function rmCopilot() {
    const c = clients[state.client];
    el.innerHTML = title('Relationship Manager Copilot', 'Grow wallet share and customer profitability.', 'CORPORATE BANKING') +
      `<div class="split">
        <div class="card list"><h2>Customer book</h2><p class="sub">Select a client</p>
          <table><thead><tr><th>Client</th><th>Loans</th><th>Profit</th><th>Risk</th></tr></thead><tbody>
          ${clients.map((cl, i) => `<tr class="clickable" data-action="client" data-idx="${i}" style="${i === state.client ? 'background:var(--blue2)' : ''}"><td><b>${cl.name}</b><br><small>${cl.industry}</small></td><td>${money(cl.loans)}</td><td>${money(cl.profitability)}</td><td>${chip(cl.riskLabel === 'Low' ? 'green' : cl.riskLabel === 'Medium' ? 'amber' : 'red', cl.riskLabel)}</td></tr>`).join('')}
          </tbody></table></div>
        <div class="detail-box">
          <h3>${c.name} <span class="chip blue">${c.industry}</span></h3>
          <div class="kpis" style="grid-template-columns:repeat(3,1fr);margin-top:10px">
            ${kpi('Deposits', money(c.deposits), 'Balance')}${kpi('Loans', money(c.loans), 'Outstanding')}${kpi('Profitability', money(c.profitability), 'Annual')}
          </div>
          <h3 style="margin-top:16px">Current products</h3>
          ${c.products.map((p) => `<div class="prod"><span>${p}</span><span class="chip blue">Active</span></div>`).join('')}
          <h3 style="margin-top:16px">Cross-sell opportunities</h3>
          ${c.suggestions.map((s) => `<div class="prod"><span>${s.p}</span><b>$${s.r}K/yr</b></div>`).join('')}
          <div class="callout"><b>Potential revenue: $${c.suggestions.reduce((a, s) => a + s.r, 0)},000 annually</b><p>Next-best products identified by the cross-sell engine.</p></div>
          <h3 style="margin-top:16px">Meeting brief</h3>
          <p style="font-size:12px;color:var(--muted);line-height:1.5">${c.brief}</p>
          <div class="callout warn"><b>Risk notifications</b><p>${c.alerts.join(' · ')}</p></div>
        </div>
      </div>`;
  }

  function underwriting() {
    const a = applications[state.app];
    el.innerHTML = title('SME Credit Underwriting Agent', 'AI-assisted credit decisions with a full audit trail.', 'CREDIT OFFICERS') +
      `<div class="split">
        <div class="card list"><h2>Application queue</h2><p class="sub">Select an application</p>
          <table><thead><tr><th>ID</th><th>Applicant</th><th>Request</th><th>Decision</th></tr></thead><tbody>
          ${applications.map((ap, i) => `<tr class="clickable" data-action="app" data-idx="${i}" style="${i === state.app ? 'background:var(--blue2)' : ''}"><td><b>${ap.id}</b></td><td>${ap.name}</td><td>${money(ap.requested)}</td><td>${chip(ap.recTone, ap.recommendation.split(' ')[0])}</td></tr>`).join('')}
          </tbody></table></div>
        <div class="detail-box">
          <h3>${a.id} — ${a.name}</h3>
          <div class="kpis" style="grid-template-columns:repeat(3,1fr);margin-top:10px">
            ${kpi('Credit score', a.score, 'of 100')}${kpi('Probability of default', a.pd + '%', '12-month')}${kpi('Requested', money(a.requested), a.industry)}
          </div>
          <h3 style="margin-top:16px">Inputs</h3>
          ${a.inputs.map((x) => `<div class="prod"><span>${x}</span><span class="chip blue">Loaded</span></div>`).join('')}
          <h3 style="margin-top:16px">Financial analysis</h3>
          ${a.metrics.map((m) => `<div class="prod"><span>${m[0]}</span><b>${m[1]}</b></div>`).join('')}
          <h3 style="margin-top:16px">Credit memo (auto-generated)</h3>
          <p style="font-size:12px;color:var(--muted);line-height:1.5">${a.memo}</p>
          <div class="callout ${a.recTone === 'red' ? 'red' : ''}"><b>Recommendation: ${a.recommendation}</b><p>Grade ${a.grade} · model confidence ${a.confidence}%</p></div>
        </div>
      </div>`;
  }

  function earlyWarning() {
    const filtered = watchlist.filter((w) => state.severity === 'All' || w.severity === state.severity);
    el.innerHTML = title('Early Warning System', 'Detect deterioration before it becomes a default.', 'RISK TEAM') +
      `<div class="kpis">${kpi('Watchlist clients', '37', 'Elevated risk')}${kpi('High severity', '9', 'Immediate review', 'bad')}${kpi('Avg distress prob.', '31%', 'Across watchlist')}${kpi('Losses avoided', '$18M', 'Est. early action', 'good')}</div>` +
      `<div class="filters">${['All', 'High', 'Medium', 'Low'].map((s) => `<button data-action="severity" data-val="${s}" class="${state.severity === s ? 'active' : ''}">${s}</button>`).join('')}</div>` +
      `<div class="card"><table><thead><tr><th>Client</th><th>Risk score</th><th>Distress prob.</th><th>Drivers</th><th>Severity</th></tr></thead><tbody>
      ${filtered.map((w) => `<tr><td><b>${w.client}</b><br><small>${w.sector}</small></td><td><b>${w.risk}/100</b><div class="bar" style="width:90px;margin-top:4px"><i style="width:${w.risk}%;background:${w.risk >= 70 ? '#dc2626' : w.risk >= 45 ? '#d97706' : '#16a34a'}"></i></div></td><td><b>${w.distress}%</b></td><td style="color:var(--muted)">${w.drivers.join(' · ')}</td><td>${chip(w.severity === 'High' ? 'red' : w.severity === 'Medium' ? 'amber' : 'green', w.severity)}</td></tr>`).join('')}
      </tbody></table></div>`;
  }

  function treasuryPage() {
    const t = treasury;
    const max = Math.max(...t.forecast.map((x) => Math.abs(x.v)));
    el.innerHTML = title('Treasury & Liquidity Copilot', 'Liquidity forecasting, funding optimization, and ALM.', 'TREASURY') +
      `<div class="kpis">${kpi('Projected funding gap', '$' + t.gap + 'M', 'Expected ' + t.date, 'bad')}${kpi('Liquidity coverage', '128%', 'LCR')}${kpi('Net stable funding', '112%', 'NSFR')}${kpi('Deposit outflow risk', 'Low', 'Stable base', 'good')}</div>` +
      `<div class="grid">
        <div class="card"><h2>Liquidity forecast</h2><p class="sub">Projected net funding position ($M)</p>
          <div class="minibars">${t.forecast.map((f) => `<div><i style="height:${(Math.abs(f.v) / max) * 100}%;background:${f.v >= 0 ? '#16a34a' : '#dc2626'}"></i><span>${f.m}</span></div>`).join('')}</div></div>
        <div class="card"><h2>Functions</h2><p class="sub">Treasury capabilities</p>
          ${['Liquidity forecasting', 'Deposit run prediction', 'Funding optimization', 'Interest-rate risk analysis', 'Capital planning'].map((f) => `<div class="prod"><span>${f}</span><span class="chip blue">Active</span></div>`).join('')}</div>
      </div>
      <div class="callout warn"><b>Recommendation: ${t.recommendation}</b><p>Projected funding gap of $${t.gap}M by ${t.date}. Issuing a 5-year bond now locks in current rates and smooths the maturity profile.</p></div>`;
  }

  function portfolioRisk() {
    const s = scenarios[state.scenario];
    const maxLoss = Math.max(...scenarios.map((x) => x.loss));
    el.innerHTML = title('Portfolio Risk Simulator', 'Enterprise stress testing across adverse scenarios.', 'CRO / SENIOR MGMT') +
      `<div class="filters">${scenarios.map((sc, i) => `<button data-action="scenario" data-idx="${i}" class="${state.scenario === i ? 'active' : ''}">${sc.name}</button>`).join('')}</div>` +
      `<div class="kpis">${kpi('Scenario', s.name, s.shock)}${kpi('Expected credit loss', '+$' + s.loss + 'M', 'vs baseline', 'bad')}${kpi('Capital ratio', s.before + '% → ' + s.after + '%', 'CET1', s.after < 10.5 ? 'bad' : 'warn')}${kpi('Below 10.5% min?', s.after < 10.5 ? 'Yes' : 'No', 'Regulatory floor', s.after < 10.5 ? 'bad' : 'good')}</div>` +
      `<div class="grid">
        <div class="card"><h2>Credit loss by scenario</h2><p class="sub">Expected credit loss ($M)</p>
          <div class="minibars">${scenarios.map((sc) => `<div><i style="height:${(sc.loss / maxLoss) * 100}%;background:${sc.id === s.id ? '#dc2626' : '#93a5bf'}"></i><span>${sc.name}</span></div>`).join('')}</div></div>
        <div class="card"><h2>All scenarios</h2><table><thead><tr><th>Scenario</th><th>Shock</th><th>Credit loss</th><th>Capital</th></tr></thead><tbody>
          ${scenarios.map((sc) => `<tr><td><b>${sc.name}</b></td><td>${sc.shock}</td><td>+$${sc.loss}M</td><td>${sc.before}% → ${sc.after}%</td></tr>`).join('')}
        </tbody></table></div>
      </div>
      <div class="callout"><b>${s.name}: ${s.shock}</b><p>Expected credit loss rises by $${s.loss}M and the CET1 ratio falls from ${s.before}% to ${s.after}%${s.after < 10.5 ? ' — below the 10.5% minimum, triggering a capital conservation review.' : '.'}</p></div>`;
  }

  function amlPage() {
    const a = alerts[state.alert];
    el.innerHTML = title('AML Investigation Agent', 'Detect and investigate suspicious activity.', 'COMPLIANCE') +
      `<div class="kpis">${kpi('Open alerts', '12', 'Case queue')}${kpi('High priority', '5', 'Escalate now', 'bad')}${kpi('SARs filed', '3', 'This quarter')}${kpi('False positive rate', '4.2%', 'Model precision', 'good')}</div>` +
      `<div class="split">
        <div class="card list"><h2>Alert queue</h2><p class="sub">Select an alert</p>
          <table><thead><tr><th>Alert</th><th>Customer</th><th>Risk</th></tr></thead><tbody>
          ${alerts.map((al, i) => `<tr class="clickable" data-action="alert" data-idx="${i}" style="${i === state.alert ? 'background:var(--blue2)' : ''}"><td><b>${al.alert}</b></td><td>${al.customer}</td><td>${chip(al.risk === 'High' ? 'red' : 'amber', al.risk)}</td></tr>`).join('')}
          </tbody></table></div>
        <div class="detail-box">
          <h3>${a.alert}</h3>
          <div class="kpis" style="grid-template-columns:repeat(2,1fr);margin-top:10px">${kpi('Customer', a.customer, '')}${kpi('Amount', a.amount, 'Flagged volume')}</div>
          <h3 style="margin-top:16px">Risk assessment</h3>
          <p style="font-size:12px;color:var(--muted);line-height:1.5">${a.note}</p>
          <div class="callout red"><b>Risk: ${a.risk}</b><p>Recommendation: ${a.rec}.</p></div>
          <h3 style="margin-top:16px">Transaction network</h3>
          <p style="font-size:12px;color:var(--muted)">5 counterparties · 14 transactions · 3 high-risk jurisdictions</p>
        </div>
      </div>`;
  }

  function stressTesting() {
    const s = stressScenarios[state.stressScenario];
    const sev = severities[state.stressSeverity];
    const loss = Math.round(s.loss * sev.mult);
    const revenue = Math.round(s.revenue * sev.mult);
    const capitalAfter = (14.2 - s.capitalDelta * sev.mult).toFixed(1);
    const lcrAfter = Math.round(128 - s.lcrDelta * sev.mult);
    const breach = parseFloat(capitalAfter) < 10.5;
    el.innerHTML = title('Stress Testing', 'Regulatory stress tests across scenarios and severities.', 'RISK TEAM') +
      `<div class="filters">${stressScenarios.map((sc, i) => `<button data-action="stress-scenario" data-idx="${i}" class="${state.stressScenario === i ? 'active' : ''}">${sc.name}</button>`).join('')}</div>` +
      `<div class="filters" style="margin-top:8px">${severities.map((sv, i) => `<button data-action="stress-severity" data-idx="${i}" class="${state.stressSeverity === i ? 'active' : ''}">${sv.name}</button>`).join('')}</div>` +
      `<div class="kpis">${kpi('Scenario', s.name, s.shock)}${kpi('Severity', sev.name, sev.mult === 0 ? 'No stress' : 'Impact ×' + sev.mult)}${kpi('Expected credit loss', '$' + loss + 'M', 'vs baseline', loss > 0 ? 'bad' : 'good')}${kpi('Net revenue impact', (revenue > 0 ? '+' : '') + '$' + revenue + 'M', 'Pre-provision', revenue < 0 ? 'bad' : 'good')}</div>` +
      `<div class="grid">
        <div class="card"><h2>Capital & liquidity</h2><p class="sub">${s.name} · ${sev.name}</p>
          <div class="prod"><span>Capital ratio (CET1)</span><b>14.2% → ${capitalAfter}%</b></div>
          <div class="prod"><span>Liquidity coverage ratio</span><b>128% → ${lcrAfter}%</b></div>
          <div class="prod"><span>Regulatory CET1 minimum</span><b>10.5%</b></div>
          <div class="prod"><span>Capital headroom after</span><b>${(parseFloat(capitalAfter) - 10.5).toFixed(1)}%</b></div>
        </div>
        <div class="card"><h2>All scenarios (Adverse)</h2><table><thead><tr><th>Scenario</th><th>Credit loss</th><th>CET1 after</th></tr></thead><tbody>
          ${stressScenarios.map((sc) => `<tr><td><b>${sc.name}</b></td><td>$${sc.loss}M</td><td>${(14.2 - sc.capitalDelta).toFixed(1)}%</td></tr>`).join('')}
        </tbody></table></div>
      </div>
      <div class="callout ${breach ? 'red' : sev.mult > 0 ? 'warn' : ''}"><b>${s.name} · ${sev.name}: ${breach ? 'Capital below minimum' : sev.mult === 0 ? 'No stress applied' : 'Within capital buffers'}</b><p>${sev.mult === 0 ? 'Baseline: CET1 14.2%, no credit losses.' : (breach ? 'CET1 falls to ' + capitalAfter + '%, below the 10.5% minimum — triggers a capital conservation review and dividend restrictions.' : 'CET1 holds at ' + capitalAfter + '%, above the 10.5% minimum.')} Expected credit loss $${loss}M.</p></div>`;
  }

  function cfoAI() {
    el.innerHTML = title('CFO AI Recommendations', 'Executive AI advisor for capital, liquidity, and risk decisions.', 'SENIOR MANAGEMENT') +
      `<div class="kpis">${kpi('Open recommendations', cfoRecs.length, 'Across 3 advisors')}${kpi('High confidence (≥80%)', cfoRecs.filter((r) => r.confidence >= 80).length, 'Act now')}${kpi('Est. value unlocked', '$24M', 'Annualized', 'good')}${kpi('Time to action', '2 weeks', 'Avg review', 'warn')}</div>` +
      cfoRecs.map((r) => `<div class="card" style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start"><div><span class="chip blue">${r.advisor}</span><h3 style="margin:8px 0 4px;font:700 14px 'Segoe UI',sans-serif">${r.action}</h3><p style="font-size:12px;color:var(--muted);margin:0">${r.reason}</p></div><span class="chip ${r.confidence >= 80 ? 'green' : r.confidence >= 70 ? 'amber' : 'red'}">${r.confidence}%</span></div><div class="meter" style="margin-top:12px"><span>Confidence</span><div class="bar"><i style="width:${r.confidence}%;background:${r.confidence >= 80 ? '#16a34a' : r.confidence >= 70 ? '#d97706' : '#dc2626'}"></i></div><b>${r.confidence}%</b></div><p style="font-size:12px;color:var(--green);margin:6px 0 0"><b>Impact:</b> ${r.impact}</p></div>`).join('');
  }

  function digitalPartners() {
    const partnerData = [
      { icon: '◆', role: 'Executive Partner', desc: 'Strategic oversight, portfolio insights, board-ready summaries, macro risk overview', color: 'var(--blue)' },
      { icon: '◇', role: 'Analyst Partner', desc: 'Automated Spreading, financial statement extraction, risk scoring, credit memos', color: 'var(--green)' },
      { icon: '◎', role: 'Service Partner', desc: 'Client 360 view, relationship health, proactive outreach, meeting briefs', color: 'var(--amber)' },
      { icon: '▪', role: 'Processor Partner', desc: 'Workflow automation, bottleneck removal, task tracking, escalation routing', color: 'var(--red)' },
      { icon: '○', role: 'Client Partner', desc: 'Borrower self-service portal, document checklists, status updates, next steps', color: '#8b5cf6' },
    ];
    const sharedTools = [
      { name: 'extract_financials', desc: 'Automated Spreading — pull structured financials from statements', icon: '📄' },
      { name: 'monitor_credit', desc: 'Continuous Credit Monitoring — real-time risk score + alerts', icon: '📡' },
      { name: 'run_credit_model', desc: 'PD model, credit score, grade assignment', icon: '📊' },
      { name: 'scan_aml_alerts', desc: 'AML/Sanctions/PEP screening, SAR generation', icon: '🔍' },
      { name: 'get_stress_test_result', desc: 'Regulatory capital projection under stress scenarios', icon: '⚡' },
      { name: 'fetch_treasury_forecast', desc: 'Liquidity forecast and funding gap analysis', icon: '💧' },
    ];
    el.innerHTML = title('Digital Partners', 'nCino-inspired agentic operating system — five specialist agents routed by an orchestrator.', 'AOS') +
      `<div class="filters"><button data-eng-auto="1" class="${state.partner ? '' : 'active'}">Auto route</button>${PARTNER_DEFS.map((p) => `<button data-eng="${esc(p.n)}" class="${state.partner === p.n ? 'active' : ''}">${esc(p.n)}</button>`).join('')}</div>` +
      `<div class="card" style="margin-bottom:16px"><h2>Architecture</h2><p class="sub">Orchestrator routes intent → specialist agent → Dual Workforce checkpoint → shared tools/memory</p>
        <div class="flow">${['User / Banker', 'Orchestrator (AOS)', 'Executive Partner', 'Analyst Partner', 'Service Partner', 'Processor Partner', 'Client Partner', 'Shared Tools'].map((s, i) => `<span class="step">${s}</span>${i < 8 ? '<span class="arrow">→</span>' : ''}`).join('')}</div></div>` +
      `<div class="grid">
        <div class="card"><h2>Specialist Partners</h2><p class="sub">Each partner is an independent agent node with its own system prompt</p>
          ${partnerData.map((p) => `<div class="prod" style="border-left:3px solid ${p.color};padding-left:10px;cursor:pointer" data-eng="${p.role}"><span>${p.icon} <b>${p.role}</b></span><small style="display:block;color:var(--muted);margin-top:2px;font-size:11px">${p.desc}</small></div>`).join('')}
          <div class="callout" style="margin-top:14px"><b>Router behavior</b><p>Intent keywords route queries: strategy/portfolio → Executive; credit/risk/financial → Analyst; client/borrower → Service; workflow/task → Processor; documents/checklist → Client. Page context acts as fallback.</p></div>
        </div>
        <div class="card"><h2>Shared Tools & Memory</h2><p class="sub">All agents access the same toolset and state store</p>
          ${sharedTools.map((t) => `<div class="prod"><span><code style="font-size:11px;background:var(--navy);color:#c7dbff;border-radius:4px;padding:1px 5px">${t.icon} ${t.name}</code></span><span style="font-size:11px;color:var(--muted)">${t.desc}</span></div>`).join('')}
          <div class="callout warn" style="margin-top:14px"><b>Dual Workforce</b><p>When risk exceeds the policy threshold, the system pauses and requires a human banker to approve or reject before proceeding. Every decision is logged in the audit trail.</p></div>
        </div>
      </div>`;
    el.querySelectorAll('[data-eng],[data-eng-auto]').forEach((c) => {
      c.onclick = () => {
        if (c.dataset.engAuto !== undefined) { state.partner = null; render(); return; }
        state.partner = c.dataset.eng;
        const p = PARTNER_DEFS.find((x) => x.n === state.partner);
        openChat(`Act as the ${state.partner} — ${p ? p.r : ''} What should I do first?`);
        render();
      };
    });
  }

  function fmtCell(v) {
    if (v === undefined || v === null || v === '') return '<span style="color:var(--muted)">—</span>';
    if (typeof v === 'number') {
      if (Number.isInteger(v)) return String(v);
      return v.toFixed(4).replace(/0+$/, '').replace(/\.$/, '');
    }
    return esc(v);
  }

  function datasetPage() {
    const recordId = '18115815';
    el.innerHTML = title('Zenodo Dataset', 'Synthetic firm-level credit-risk dataset — metadata, feature profile & sample preview fetched live from the Zenodo REST API (no full download).', 'LIVE API') +
      `<div class="kpis" id="zenKpis">${kpi('Record', recordId, 'Zenodo ID')}${kpi('Source', 'Zenodo', 'Open repository')}${kpi('Fetch mode', 'Metadata + sample', 'No full download', 'good')}${kpi('Firms', '…', 'Loading…')}${kpi('Features', '…', 'Loading…')}</div>` +
      `<div class="card" id="zenMeta"><h2>Dataset metadata</h2><p class="sub">Loading from Zenodo…</p></div>` +
      `<div class="card" id="zenSample" style="margin-top:16px"><h2>Sample data</h2><p class="sub">Previewing the first rows — no full dataset downloaded</p><div style="padding:16px;color:var(--muted);font-size:12px">Fetching sample…</div></div>` +
      `<div class="card" id="zenFeatures" style="margin-top:16px"><h2>Feature profile</h2><p class="sub">Loading…</p></div>`;

    const metaBox = el.querySelector('#zenMeta');
    const sampleBox = el.querySelector('#zenSample');
    const kpiBox = el.querySelector('#zenKpis');
    const featBox = el.querySelector('#zenFeatures');

    Promise.all([
      fetch(`${API}/api/zenodo/${recordId}`).then((r) => r.json()),
      fetch(`${API}/api/zenodo/${recordId}/stats`).then((r) => r.json()).catch(() => null),
    ]).then(([d, stats]) => {
        if (d.error) throw new Error(d.error);
        const mb = (d.total_size / (1024 * 1024)).toFixed(2);
        const firms = stats && stats.firms ? stats.firms.toLocaleString() : '—';
        const features = stats && stats.features ? stats.features : '—';
        const featureNames = (stats && stats.columns) || [];
        kpiBox.innerHTML = kpi('Views', (d.stats.views || 0).toLocaleString(), 'Zenodo total') +
          kpi('Downloads', (d.stats.downloads || 0).toLocaleString(), 'Zenodo total') +
          kpi('Files', d.files.length, 'Total ' + mb + ' MB') +
          kpi('Firms', firms, stats ? 'Rows in source file' : 'Could not count') +
          kpi('Features', features, stats ? 'Feature columns' : 'Could not count');
        if (featureNames.length) {
          featBox.innerHTML = `<h2>Feature profile</h2><p class="sub">${features} feature columns identified from the source file header</p>` +
            `<div class="grid" style="gap:12px 24px;margin-top:8px">${featureNames.map((f) => `<div class="prod"><span><code style="font-size:11px;background:var(--navy);color:#c7dbff;border-radius:4px;padding:1px 5px">${esc(f)}</code></span></div>`).join('')}</div>`;
        }
        metaBox.innerHTML = `<h2>${esc(d.title)}</h2><p class="sub">${esc(d.resource_type)} · published ${esc(d.publication_date)}</p>
          <div class="grid" style="gap:0 24px">
            <div class="prod"><span>DOI</span><b>${esc(d.doi)}</b></div>
            <div class="prod"><span>License</span><span class="chip green">${esc(d.license)}</span></div>
            <div class="prod"><span>Access</span><b>${esc(String(d.access_right).toUpperCase())}</b></div>
            <div class="prod"><span>Creator(s)</span><b>${esc(d.creators.join(', ') || 'N/A')}</b></div>
          </div>
          <h3 style="margin:16px 0 6px">Description</h3>
          <p style="font-size:12px;color:var(--muted);line-height:1.6;margin:0">${esc(d.description.slice(0, 900))}${d.description.length > 900 ? '…' : ''}</p>
          <h3 style="margin:16px 0 6px">Files (not downloaded)</h3>
          ${d.files.map((f) => `<div class="prod"><span><code style="font-size:11px;background:var(--navy);color:#c7dbff;border-radius:4px;padding:1px 5px">${esc(f.key)}</code></span><b>${(f.size / (1024 * 1024)).toFixed(2)} MB</b></div>`).join('')}
          <div class="callout"><b>Retrieved via the Zenodo REST API</b><p>No data files were downloaded — only metadata plus a small HTTP Range preview of the first file.</p></div>`;
      })
      .catch((e) => {
        metaBox.innerHTML = `<h2>Dataset metadata</h2><div class="callout red"><b>Could not reach the backend</b><p>Start the server with <code>npm start</code> so the app can proxy the Zenodo API. (${esc(e.message)})</p></div>`;
      });

    fetch(`${API}/api/zenodo/${recordId}/sample`)
      .then((r) => r.json())
      .then((d) => {
        if (d.error) throw new Error(d.error);
        const cols = d.columns.slice(0, 13);
        const kb = (d.bytesFetched / 1024).toFixed(0);
        sampleBox.innerHTML = `<h2>Sample data — <code style="font-size:11px;background:var(--bg);padding:1px 5px;border-radius:4px">${esc(d.file || '')}</code></h2>
          <p class="sub">First ${d.rows.length} rows · ${cols.length} columns · fetched ${kb} KB via HTTP Range (no full download)</p>
          <div style="overflow:auto"><table><thead><tr>${cols.map((c) => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>
          ${d.rows.map((row) => `<tr>${cols.map((_, i) => `<td>${fmtCell(row[i])}</td>`).join('')}</tr>`).join('')}
          </tbody></table></div>
          <div class="callout warn"><b>Note on formatting</b><p>The source CSV uses European decimal commas (e.g. <code>"7229,321243"</code>); values are normalized to standard decimals for display. <b>Status</b> is the event indicator (1 = event/default, 0 = censored) and <b>hazard</b> is the modeled credit-risk hazard rate.</p></div>`;
      })
      .catch((e) => {
        sampleBox.innerHTML = `<h2>Sample data</h2><div class="callout red"><b>Sample unavailable</b><p>${esc(e.message)}</p></div>`;
      });
  }

  const pages = { Overview: overview, 'RM Copilot': rmCopilot, 'Credit Underwriting': underwriting, 'Early Warning': earlyWarning, Treasury: treasuryPage, 'Portfolio Risk': portfolioRisk, 'Stress Testing': stressTesting, 'CFO AI': cfoAI, AML: amlPage, 'Digital Partners': digitalPartners, Dataset: datasetPage };

  /* ============ AI AGENT LAYER ============ */
  const API = 'http://localhost:3000';
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  let backendOk = null;

  async function checkBackend() {
    try {
      const r = await fetch(API + '/api/agent/health', { signal: AbortSignal.timeout(1200) });
      const j = await r.json();
      backendOk = Boolean(j.ok);
    } catch (e) { backendOk = false; }
  }

  /* local deterministic agent engine (used when the backend is off) */
  const AGENT_ROSTER = [
    { n: 'Executive Partner', r: 'Strategic overview, portfolio insights, board-ready summaries' },
    { n: 'Analyst Partner', r: 'Deep financial analysis, spreading, risk scoring, credit memos' },
    { n: 'Service Partner', r: 'Client 360, relationship health, proactive outreach' },
    { n: 'Processor Partner', r: 'Workflow automation, bottleneck removal, task tracking' },
    { n: 'Client Partner', r: 'Borrower self-service, status, required documents, next steps' },
    { n: 'Credit Underwriting Agent', r: 'Analyze financial statements, score credit, estimate PD' },
    { n: 'Risk Assessment Agent', r: 'Early-warning detection, stress testing, capital adequacy' },
    { n: 'Compliance (AML) Agent', r: 'Suspicious activity, sanctions/PEP screening, SARs' },
    { n: 'Treasury & Liquidity Agent', r: 'Liquidity forecasting, funding gaps, ALM' },
    { n: 'Relationship Manager Copilot', r: 'Client 360, cross-sell, meeting briefs' },
    { n: 'CFO Advisor', r: 'Capital planning and executive recommendations' },
  ];

  const PARTNER_DEFS = AGENT_ROSTER.slice(0, 5);

  /* Orchestrator (AOS) — routes a request to the right Digital Partner by intent */
  function routePartner(text, page) {
    if (state.partner && PARTNER_DEFS.some((p) => p.n === state.partner)) return state.partner;
    const q = (text || '').toLowerCase();
    if (/executive|strategy|portfolio|insight|board|macro|overview/.test(q)) return 'Executive Partner';
    if (/analyz|spread|financial|risk|credit|underwrit|pd\b|score|loan/.test(q)) return 'Analyst Partner';
    if (/client|borrower|customer|service|relationship|outreach/.test(q)) return 'Service Partner';
    if (/process|workflow|bottleneck|automation|task|escalat|approval/.test(q)) return 'Processor Partner';
    if (/document|what do i need|checklist|self.?service|apply|next steps/.test(q)) return 'Client Partner';
    const byPage = {
      'RM Copilot': 'Service Partner',
      'Credit Underwriting': 'Analyst Partner',
      'Early Warning': 'Analyst Partner',
      Treasury: 'Analyst Partner',
      'Portfolio Risk': 'Executive Partner',
      'Stress Testing': 'Executive Partner',
      'CFO AI': 'Executive Partner',
      AML: 'Processor Partner',
      'Digital Partners': 'Executive Partner',
      Dataset: 'Analyst Partner',
    };
    return byPage[page] || 'Service Partner';
  }

  function currentContext() {
    const p = state.page;
    if (p === 'RM Copilot') { const c = clients[state.client]; return `RM Copilot · reviewing client ${c.name} (${c.industry}). Deposits ${money(c.deposits)}, loans ${money(c.loans)}, profitability ${money(c.profitability)}. Products: ${c.products.join(', ')}. Cross-sell candidates: ${c.suggestions.map((s) => s.p).join(', ')}. Risk: ${c.riskLabel}. Alerts: ${c.alerts.join('; ')}.`; }
    if (p === 'Credit Underwriting') { const a = applications[state.app]; return `Credit Underwriting · evaluating ${a.id} ${a.name} (${a.industry}), $${a.requested}M requested. Score ${a.score}/100, PD ${a.pd}%, grade ${a.grade}. Metrics: ${a.metrics.map((m) => `${m[0]} ${m[1]}`).join('; ')}.`; }
    if (p === 'Early Warning') { const w = watchlist.find((x) => x.severity === state.severity) || watchlist[0]; return `Early Warning · filter ${state.severity}. Example client ${w.client} risk ${w.risk}/100, distress ${w.distress}%. Drivers: ${w.drivers.join('; ')}.`; }
    if (p === 'Treasury') return `Treasury · projected funding gap $${treasury.gap}M by ${treasury.date}. LCR 128%. Forecast: ${treasury.forecast.map((f) => `${f.m} ${f.v}`).join(', ')}. Recommendation: ${treasury.recommendation}.`;
    if (p === 'Portfolio Risk') { const s = scenarios[state.scenario]; return `Portfolio Risk · scenario ${s.name} (${s.shock}). Credit loss +$${s.loss}M, CET1 ${s.before}%→${s.after}%.`; }
    if (p === 'Stress Testing') { const s = stressScenarios[state.stressScenario]; const sv = severities[state.stressSeverity]; return `Stress Testing · ${s.name} (${s.shock}) at ${sv.name} severity. Loss $${Math.round(s.loss * sv.mult)}M, revenue $${Math.round(s.revenue * sv.mult)}M.`; }
    if (p === 'CFO AI') return `CFO AI · top recommendation: ${cfoRecs[0].action} (${cfoRecs[0].confidence}% confidence, presented by ${cfoRecs[0].advisor}). ${cfoRecs[0].reason}`;
    if (p === 'AML') { const a = alerts[state.alert]; return `AML · investigating ${a.alert} on ${a.customer}. Amount ${a.amount}, risk ${a.risk}. Note: ${a.note}`; }
    if (p === 'Digital Partners') { return `Digital Partners · orchestration architecture. Active partner: ${state.partner || 'router (auto)'}. Five specialist roles: Executive, Analyst, Service, Processor, Client. Shared tools: extract_financials (Automated Spreading), monitor_credit (Continuous Credit Monitoring), run_credit_model, scan_aml_alerts, get_stress_test_result, fetch_treasury_forecast. Dual Workforce: human-review checkpoint for elevated risk.`; }
    if (p === 'Dataset') return 'Zenodo Dataset · synthetic firm-level credit-risk data (record 18115815). ~20,000 synthetic firms with sectors, regions, financials, and credit hazard scores. Source: Zenodo REST API. Data NOT downloaded — only metadata + sample preview via HTTP Range.';
    return 'Executive overview of the BankRisk platform across the commercial lending lifecycle.';
  }

  async function localAgent(query, context) {
    const q = (query || '').toLowerCase();
    const has = (...ks) => ks.some((k) => q.includes(k));

    if (has('watchlist', 'early', 'warning', 'deteriorate', 'default')) {
      const w = watchlist[0];
      return {
        summary: `Zeta Retail is the highest-watchlist name: risk score 81/100 with a 67% distress probability. Revenue decline and increased overdraft usage are the dominant triggers. Recommend a heightened monitoring plan and a repayment review within 30 days.`,
        steps: [
          { title: 'Scanned watchlist', detail: `Loaded ${watchlist.length} clients by severity` },
          { title: 'Ranked by risk score', detail: `${w.client} tops the list at ${w.risk}/100` },
          { title: 'Extracted deterioration drivers', detail: w.drivers.join('; ') },
          { title: 'Recommended action', detail: 'Risk-team review and account-level restructuring' },
        ],
        tools: [
          { name: 'query_database', args: 'watchlist, severity=High', status: 'complete' },
          { name: 'run_credit_model', args: `portfolio: ${w.client}`, status: 'complete' },
        ],
        agents: [
          { name: 'Risk Assessment Agent', role: 'scored distress probability', status: 'complete' },
          { name: 'Relationship Manager Copilot', role: 'prepared client review notes', status: 'complete' },
        ],
        confidence: 86,
        evidence: [`${w.client} risk score ${w.risk}/100`, `Distress probability ${w.distress}%`, `Drivers: ${w.drivers.slice(0, 2).join('; ')}`],
        recommendations: ['Schedule a 30-day account review', 'Draft restructuring options', 'Notify relationship manager'],
        routedTo: 'Analyst Partner',
        humanApprovalNeeded: true,
      };
    }

    if (has('aml', 'suspicious', 'compliance', 'sar', 'sanction', 'money', 'fraud', 'alert')) {
      const a = alerts[state.alert] || alerts[0];
      return {
        summary: `${a.alert} on ${a.customer} ($${a.amount}) rates ${a.risk} risk. ${a.note} Recommendation: ${a.rec}.`,
        steps: [
          { title: 'Prioritized alert queue', detail: `${a.risk} severity promoted first` },
          { title: 'Mapped transaction network', detail: '5 counterparties · 14 transactions · 3 high-risk jurisdictions' },
          { title: 'Applied typology match', detail: a.alert },
          { title: 'Drafted disposition', detail: a.rec },
        ],
        tools: [
          { name: 'scan_aml_alerts', args: a.customer, status: 'complete' },
          { name: 'monitor_credit', args: a.customer + ' · continuous', status: 'complete' },
          { name: 'query_database', args: 'transactions, 30-day window', status: 'complete' },
        ],
        agents: [
          { name: 'Compliance (AML) Agent', role: 'typology detection and risk scoring', status: 'complete' },
          { name: 'Risk Assessment Agent', role: 'validated customer risk', status: 'complete' },
        ],
        confidence: a.risk === 'High' ? 93 : 78,
        evidence: [`Volume ${a.amount}`, a.note, `Customer ${a.customer}`],
        recommendations: [a.rec, 'Document rationale in audit trail', 'Re-score customer risk quarterly'],
        routedTo: 'Processor Partner',
        humanApprovalNeeded: a.risk !== 'Low',
      };
    }

    if (has('treasury', 'liquidity', 'gap', 'funding', 'bond', 'lcr', 'nsfr', 'liquidity coverage')) {
      return {
        summary: `Projected funding gap of $${treasury.gap}M by ${treasury.date} with LCR at 128% and NSFR at 112%. Recommendation: ${treasury.recommendation} to lock in current rates and smooth the maturity profile.`,
        steps: [
          { title: 'Loaded liquidity forecast', detail: '8-month projected net funding positions' },
          { title: 'Identified gap month', detail: `Gap crosses zero at M5, low of $${treasury.gap}M at M8` },
          { title: 'Assessed LCR/NSFR headroom', detail: '128% / 112% vs regulatory floors' },
          { title: 'Selected funding strategy', detail: treasury.recommendation },
        ],
        tools: [
          { name: 'fetch_treasury_forecast', args: 'next 8 months', status: 'complete' },
          { name: 'query_database', args: 'liquidity buffers', status: 'complete' },
        ],
        agents: [
          { name: 'Treasury & Liquidity Agent', role: 'ran forecast and gap analysis', status: 'complete' },
          { name: 'CFO Advisor', role: 'validated funding recommendation', status: 'complete' },
        ],
        confidence: 85,
        evidence: [`Funding gap $${treasury.gap}M by ${treasury.date}`, 'LCR 128% headroom', 'Rate lock opportunity'],
        recommendations: [treasury.recommendation, 'Review short-term maturity ladder', 'Deploy excess cash into HQLA'],
        routedTo: 'Analyst Partner',
        humanApprovalNeeded: false,
      };
    }

    if (
      q.includes('stress') || q.includes('capital') || q.includes('cet1') ||
      q.includes('scenario') || q.includes('recession') || q.includes('severe') ||
      q.includes('commercial real') || q.includes('breach') || q.includes('buffer')
    ) {
      const s = stressScenarios[state.stressScenario];
      const breach = (14.2 - s.capitalDelta) < 10.5;
      return {
        summary: `Under ${s.name} (${s.shock}), expected credit loss is ~$${s.loss}M and CET1 falls from 14.2% to ${(14.2 - s.capitalDelta).toFixed(1)}% — ${breach ? 'below' : 'above'} the 10.5% regulatory minimum${breach ? ', triggering a capital conservation review' : ''}.`,
        steps: [
          { title: 'Loaded stress scenario', detail: `${s.name}: ${s.shock}` },
          { title: 'Applied portfolio shocks', detail: `Credit loss +$${s.loss}M` },
          { title: 'Projected capital impact', detail: `CET1 ${(14.2 - s.capitalDelta).toFixed(1)}% after stress` },
          { title: 'Checked regulatory floor', detail: breach ? 'Breach → capital action required' : 'Within the 10.5% floor' },
        ],
        tools: [
          { name: 'get_stress_test_result', args: s.name.toLowerCase(), status: 'complete' },
          { name: 'run_credit_model', args: 'enterprise portfolio', status: 'complete' },
        ],
        agents: [
          { name: 'Risk Assessment Agent', role: 'ran scenario and capital projection', status: 'complete' },
          { name: 'CFO Advisor', role: 'translated to capital-planning action', status: 'complete' },
        ],
        confidence: 82,
        evidence: [`$${s.loss}M expected credit loss`, `CET1 ${(14.2 - s.capitalDelta).toFixed(1)}%`, `${s.shock} shock applied`],
        recommendations: breach
          ? ['Increase loan-loss provisions', 'Raise additional Tier 1 capital', 'Reduce sector concentration']
          : ['Maintain provisions', 'Monitor CRE segment closely', 'Run quarterly re-test'],
        routedTo: 'Executive Partner',
        humanApprovalNeeded: breach,
      };
    }

    if (has('delta foods', 'credit', 'application', 'approve', 'underwrit', 'pd', 'score', 'loan')) {
      const a = applications[state.app];
      return {
        summary: `${a.name} (${a.id}): score ${a.score}/100, PD ${a.pd}%, grade ${a.grade}. ${a.recommendation}. Model confidence ${a.confidence}%.`,
        steps: [
          { title: 'Pulled applicant records', detail: `${a.inputs.length} documents loaded` },
          { title: 'Computed core ratios', detail: a.metrics.map((m) => `${m[0]} ${m[1]}`).join('; ') },
          { title: 'Scored application', detail: `${a.score}/100 → grade ${a.grade}` },
          { title: 'Drafted recommendation', detail: a.recommendation },
        ],
        tools: [
          { name: 'extract_financials', args: `${a.id} · statements + tax returns`, status: 'complete' },
          { name: 'run_credit_model', args: a.id + ' · Automated Spreading → PD model', status: 'complete' },
          { name: 'monitor_credit', args: a.name + ' · continuous monitoring', status: 'complete' },
        ],
        agents: [
          { name: 'Credit Underwriting Agent', role: 'Automated Spreading + financial analysis and scoring', status: 'complete' },
          { name: 'Risk Assessment Agent', role: 'validated exposure', status: 'complete' },
        ],
        confidence: a.confidence,
        evidence: a.metrics.slice(0, 3).map((m) => `${m[0]} ${m[1]}`),
        recommendations: [a.recommendation, `Grade ${a.grade} · PD ${a.pd}%`, 'Attach audit trail to credit file'],
        routedTo: 'Analyst Partner',
        humanApprovalNeeded: !a.recommendation.startsWith('Approve'),
      };
    }

    if (has('client', 'customer', 'deposit', 'deposits', 'profit', 'cross-sell', 'sell', 'esg', 'rm ')) {
      const c = clients[state.client];
      const rev = c.suggestions.reduce((a, s) => a + s.r, 0);
      return {
        summary: `${c.name} (${c.industry}) holds ${money(c.deposits)} in deposits and ${money(c.loans)} in loans with annual profitability of ${money(c.profitability)}. Risk is rated ${c.riskLabel}. Cross-sell potential: ${rev}K/yr. ${c.brief}`,
        steps: [
          { title: 'Built client 360', detail: `${money(c.deposits)} deposits · ${money(c.loans)} loans · ${money(c.profitability)} profit/yr` },
          { title: 'Scored relationship profitability', detail: `${c.products.length} products held` },
          { title: 'Matched next-best products', detail: c.suggestions.map((s) => s.p).join(', ') },
          { title: 'Drafted meeting brief', detail: 'Key risks and opportunities surfaced' },
        ],
        tools: [
          { name: 'query_database', args: `client_360, ${c.name}`, status: 'complete' },
          { name: 'monitor_credit', args: c.name + ' · relationship health', status: 'complete' },
          { name: 'run_credit_model', args: `relationship: ${c.name}`, status: 'complete' },
        ],
        agents: [
          { name: 'Relationship Manager Copilot', role: 'client 360 and cross-sell engine', status: 'complete' },
          { name: 'Risk Assessment Agent', role: 'validated risk label', status: 'complete' },
        ],
        confidence: 84,
        evidence: [`Deposits ${money(c.deposits)}`, `Loans ${money(c.loans)}`, `Profitability ${money(c.profitability)}`],
        recommendations: [`Close ${c.suggestions[0].p} (est. $${c.suggestions[0].r}K/yr)`, 'Review risk notifications before meeting', 'Log meeting brief to CRM'],
        routedTo: 'Service Partner',
        humanApprovalNeeded: false,
      };
    }

    if (q.includes('zenodo') || q.includes('dataset') || q.includes('synthetic firm')) {
      let firms = '~20,000';
      let feats = '13';
      let cols = [];
      const stats = await fetch(`${API}/api/zenodo/18115815/stats`).then((r) => r.json()).catch(() => null);
      if (stats && !stats.error && stats.firms) {
        firms = stats.firms.toLocaleString();
        feats = String(stats.features);
        cols = stats.columns || [];
      }
      const colList = cols.length ? cols.join(', ') : 'Sector, Region, Leverage, Profit_Margin, hazard, Event_Time, Status';
      return {
        summary: `Zenodo record 18115815 holds a fully synthetic firm-level credit-risk dataset: exactly **${firms} firms** in the source file (\`firms_features_clean.csv\`) with **${feats} feature columns** — ${colList}. Companies span Services, Technology, Manufacturing, Retail, Energy, Finance, and more, in Europe, Latin America, and the USA. Key risk features include leverage, profit margin, R&D intensity, organizational complexity, a survival-model hazard score, and an event indicator (Status: 1 = event/default, 0 = censored). Because the data is synthetic, it is safe for model prototyping and UI demos, but must not be used as real customer data.`,
        steps: [
          { title: 'Hit the Zenodo REST API', detail: 'Fetched metadata only — no bulk download' },
          { title: 'Counted rows in the source file', detail: `${firms} firms (header + data rows parsed server-side)` },
          { title: 'Profile the schema', detail: `${feats} feature columns identified from the header` },
          { title: 'Normalized European decimals', detail: '"7229,321243" → 7229.32' },
        ],
        tools: [
          { name: 'query_database', args: 'zenodo/records/18115815', status: 'complete' },
          { name: 'count_rows', args: 'firms_features_clean.csv → ' + firms + ' firms', status: 'complete' },
          { name: 'count_features', args: 'header → ' + feats + ' columns', status: 'complete' },
          { name: 'extract_financials', args: 'sample rows · Automated Spreading', status: 'complete' },
        ],
        agents: [
          { name: 'Analyst Partner', role: 'profiled the dataset schema and risk fields', status: 'complete' },
          { name: 'Processor Partner', role: 'counted firms and features in the source', status: 'complete' },
          { name: 'Executive Partner', role: 'framed safe-use guidance', status: 'complete' },
        ],
        confidence: 92,
        evidence: [`${firms} synthetic firms (exact row count)`, `${feats} feature columns: ${colList}`, 'Hazard score + event indicator (Status) columns'],
        recommendations: ['Use only for prototyping / demos', 'Treat as synthetic — never use as real customer data', 'Load sample into the credit model sandbox'],
        routedTo: 'Analyst Partner',
        humanApprovalNeeded: false,
      };
    }

    /* generic overview answer */
    const s = scenarios[state.scenario];
    return {
      summary: `Executive view: 1,248 active clients, $2.4B loan book, weighted PD 2.6%, CET1 14.2%. Under the ${s.name} scenario (${s.shock}), credit losses rise $${s.loss}M and CET1 falls to ${s.after}%.`,
      steps: [
        { title: 'Aggregated portfolio KPIs', detail: 'Clients, loan book, PD, capital' },
        { title: 'Ranked active risks', detail: 'Watchlist 37 · AML alerts 12' },
        { title: 'Ran portfolio simulation', detail: `${s.name}: CET1 → ${s.after}%` },
        { title: 'Synthesized executive summary', detail: 'Dashboards updated' },
      ],
      tools: [
        { name: 'query_database', args: 'portfolio index', status: 'complete' },
        { name: 'extract_financials', args: 'top 20 obligors · Automated Spreading', status: 'complete' },
        { name: 'get_stress_test_result', args: s.name.toLowerCase(), status: 'complete' },
      ],
      agents: [
        { name: 'Risk Assessment Agent', role: 'aggregated portfolio metrics', status: 'complete' },
        { name: 'CFO Advisor', role: 'framed executive insight', status: 'complete' },
      ],
      confidence: 78,
      evidence: [`CET1 ${s.before}% base`, `PD 2.6% portfolio`, `${s.loss}M loss in ${s.name}`],
      recommendations: ['Review CPI dashboard', 'Review top watchlist names', 'Pre-read CFO AI recommendations'],
      routedTo: routePartner(query, state.page),
      humanApprovalNeeded: false,
    };
  }

  async function agentAnalyze(query, context) {
    if (backendOk) {
      try {
        const r = await fetch(API + '/api/agent/analyze', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, context }),
        });
        const j = await r.json();
        if (j.error) throw new Error(j.error);
        return overrideRoute(j);
      } catch (e) { backendOk = false; }
    }
    return overrideRoute(await localAgent(query, context));
  }

  function overrideRoute(data) {
    if (state.partner && PARTNER_DEFS.some((p) => p.n === state.partner)) {
      data.routedTo = state.partner;
    }
    return data;
  }

  /* ---------- agent workflow renderer with progressive reveal ---------- */
  function esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

  function agentRunHTML(data, heading) {
    const dw = data.humanApprovalNeeded;
    return `<div class="agent-run">
      <div class="agent-head"><b>${esc(heading)}</b><span class="conf-label">conf ${data.confidence || 0}%</span></div>
      <div class="agent-router" data-r="router">Orchestrator → <b>${esc(data.routedTo || 'Service Partner')}</b></div>
      <ol class="agent-steps">${data.steps.map((s) => `<li data-r="step"><span class="dot">◇</span><div><div class="label">${esc(s.title)}</div><div class="detail">${esc(s.detail)}</div></div></li>`).join('')}</ol>
      <div class="agent-tools">${data.tools.map((t) => `<div class="tool-call" data-r="tool"><span><b>${esc(t.name)}</b>(${esc(t.args)})</span><span class="status">queued</span></div>`).join('')}</div>
      ${data.agents.length ? `<div class="agent-handoff">${data.agents.map((a) => `<span class="node" data-r="hand"><span class="dot">✦</span>${esc(a.name)}<small>${esc(a.role)}</small></span>`).join('')}</div>` : ''}
      <div class="conf-box" data-r="conf"><b>${data.confidence || 0}%</b><div><div class="bar"><i style="width:0;background:${(data.confidence || 0) >= 80 ? '#16a34a' : (data.confidence || 0) >= 60 ? '#d97706' : '#dc2626'}"></i></div><small>model confidence</small></div></div>
      <div data-r="evi">
        <p style="font-size:12px;color:var(--muted);font-weight:700;margin:14px 0 4px">Evidence</p>
        <ul class="evidence">${data.evidence.map((e) => `<li style="opacity:0">${esc(e)}</li>`).join('')}</ul>
      </div>
      <div data-r="recs">
        <p style="font-size:12px;color:var(--muted);font-weight:700;margin:14px 0 6px">Recommended actions</p>
        <div class="recs">${data.recommendations.map((r) => `<div class="rec" style="opacity:0">✓ ${esc(r)}</div>`).join('')}</div>
      </div>
      ${dw ? `<div class="dw-checkpoint" data-r="dw" style="opacity:0">
        <div class="dw-icon">⚠ Dual Workforce Checkpoint</div>
        <p>The analyst team elevated this case to a <b>human-in-the-loop review</b>. A banker must approve or reject before the recommendation proceeds.</p>
        <div class="dw-actions">
          <button class="dw-approve" data-dw="approve">✓ Approve</button>
          <button class="dw-reject" data-dw="reject">✕ Reject</button>
        </div>
        <span class="dw-result"></span>
      </div>` : ''}
    </div>`;
  }

  async function animateAgentRun(el, data, heading) {
    el.insertAdjacentHTML('beforeend', await agentRunHTML(data, heading));
    const panel = el.lastElementChild;
    const router = panel.querySelector('[data-r="router"]');
    const steps = panel.querySelectorAll('[data-r="step"]');
    const tools = panel.querySelectorAll('[data-r="tool"]');
    const hands = panel.querySelectorAll('[data-r="hand"]');
    const conf = panel.querySelector('[data-r="conf"]');
    const evis = panel.querySelectorAll('[data-r="evi"] li');
    const recs = panel.querySelectorAll('[data-r="recs"] .rec');
    const dw = panel.querySelector('[data-r="dw"]');

    if (router) { router.style.opacity = 0; }
    steps.forEach((s) => s.classList.add('prep'));
    tools.forEach((t) => { t.style.opacity = 0; });
    hands.forEach((h) => { h.style.opacity = 0; });
    if (conf) conf.style.opacity = 0;
    if (dw) dw.style.opacity = 0;

    await sleep(200);
    if (router) { router.style.transition = 'opacity .3s'; router.style.opacity = 1; await sleep(220); }
    for (const [i, s] of steps.entries()) {
      s.classList.remove('prep');
      s.classList.add('active');
      if (i === steps.length - 1 && tools.length === 0) { s.classList.add('done'); }
      s.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      await sleep(620);
      s.classList.replace('active', 'done');
    }
    for (const [i, t] of tools.entries()) {
      t.style.opacity = 1;
      const st = t.querySelector('.status');
      st.textContent = 'running'; st.className = 'status running';
      await sleep(450);
      st.textContent = 'complete'; st.className = 'status complete';
    }
    for (const [i, h] of hands.entries()) {
      h.style.opacity = 1;
      if (i === hands.length - 1) { h.classList.add('active'); }
      else { h.classList.add('done'); }
      await sleep(400);
      h.classList.add('done'); h.classList.remove('active');
    }
    if (conf) {
      conf.style.opacity = 1;
      const bar = conf.querySelector('.bar i');
      await sleep(120);
      bar.style.width = `${data.confidence || 0}%`;
      bar.style.transition = 'width .9s ease';
    }
    for (const e of evis) { e.style.transition = 'opacity .3s'; e.style.opacity = 1; await sleep(70); }
    await sleep(150);
    for (const r of recs) { r.style.transition = 'opacity .3s'; r.style.opacity = 1; await sleep(90); }
    if (dw) {
      await sleep(300);
      dw.style.transition = 'opacity .3s';
      dw.style.opacity = 1;
      dw.querySelectorAll('[data-dw]').forEach((btn) => {
        btn.onclick = () => {
          const verdict = btn.dataset.dw;
          dw.querySelectorAll('[data-dw]').forEach((b) => { b.disabled = true; });
          btn.classList.add('dw-selected');
          const ts = new Date().toLocaleTimeString();
          dw.querySelector('.dw-result').textContent = verdict === 'approve'
            ? `✓ Approved by Risk Officer · ${ts}`
            : `✕ Rejected — escalation queued · ${ts}`;
          dw.querySelector('.dw-result').className = 'dw-result ' + verdict;
        };
      });
    }
    panel.querySelectorAll('.agent-steps, .agent-tools, .agent-handoff, [data-r="evi"], [data-r="recs"], .conf-box').forEach((x) => { x.style.visibility = 'visible'; });
  }

  /* ---------- per-page AI widget ---------- */
  const AI_WIDGETS = {
    'RM Copilot': ['What should I focus on with ' + clients[0].name + '?', 'Cross-sell ideas for ' + clients[0].name],
    'Credit Underwriting': ['Summarize the current application?', 'What conditions should I attach?'],
    'Early Warning': ['Which client is deteriorating fastest?', 'How to downgrade a watchlist name?'],
    Treasury: ['When is the funding gap worst?', 'Should we issue a bond?'],
    'Portfolio Risk': ['Most damaging scenario?', 'Which sector to de-risk?'],
    'Stress Testing': ['Will we breach the CET1 floor?', 'What capital action first?'],
    'CFO AI': ['What should the CFO act on today?', 'Trade-offs of raising AT1?'],
    AML: ['What is the top alert?', 'Should we file a SAR?'],
    'Digital Partners': ['How do the five partners divide work?', 'Which partner handles document collection?'],
    Dataset: ['Summarize the dataset', 'Is sector risk evenly spread?', 'What drives the hazard score?'],
    Overview: ['What is the top risk right now?', 'Summarize the platform'],
  };

  function addAgentWidget() {
    const ctx = currentContext();
    const suggestions = AI_WIDGETS[state.page] || ['Summarize this page'];
    const widget = document.createElement('div');
    widget.className = 'agent-run';
    widget.id = 'pageWidget';
    widget.innerHTML = `<div class="agent-head"><b>✦ Agent team — ${state.page}</b><span class="agent-status" data-ai="run"><span class="agent-pulse">●</span> Run AI analysis</span></div>
      <p style="font-size:12px;color:var(--muted);margin:6px 0 0">Ask the agent team about this module. Results stream with reasoning steps, tool calls, and agent handoffs.</p>
      <div class="chat-suggestions" style="padding:10px 0 0">${suggestions.map((s) => `<button data-ai="ask" data-q="${esc(s)}">${esc(s)}</button>`).join('')}</div>
      <div data-result=""></div>`;
    el.appendChild(widget);

    widget.querySelector('[data-ai="run"]').onclick = async () => await runAgentInto(widget, 'AI analysis — ' + state.page, 'Run a full analysis on the current view. ' + ctx);
    widget.querySelectorAll('[data-ai="ask"]').forEach((b) => {
      b.onclick = () => widget.querySelector('[data-ai="run"]').click();
    });
  }

  async function runAgentInto(container, heading, prompt) {
    const resultBox = container.querySelector('[data-result]');
    const runBtn = container.querySelector('[data-ai="run"]');
    if (runBtn) { runBtn.disabled = true; runBtn.querySelector('.agent-pulse').classList.add('done'); }
    await animateAgentRun(resultBox, await agentAnalyze(prompt, currentContext()), heading);
    if (runBtn) { runBtn.disabled = false; runBtn.querySelector('.agent-pulse').classList.remove('done'); runBtn.querySelector('.agent-pulse').classList.add('done'); }
  }

  /* ---------- chat ---------- */
  const chat = { messages: [{ role: 'system', content: 'You are the BankRisk agent team. Answer concisely with banking expertise and always state supporting evidence and confidence.' }], busy: false };
  const chatBody = () => document.getElementById('chatBody');
  const chatInput = () => document.getElementById('chatInput');
  const chatSend = () => document.getElementById('chatSend');

  function syncSuggestions() {
    const box = document.getElementById('chatSuggestions');
    box.innerHTML = (AI_WIDGETS[state.page] || ['Summarize this page']).slice(0, 2).map((s) => `<button data-q="${esc(s)}">${esc(s)}</button>`).join('');
  }

  function pushMsg(html, cls) {
    const m = document.createElement('div');
    m.className = 'msg ' + (cls || 'agent');
    m.innerHTML = html;
    chatBody().appendChild(m);
    chatBody().scrollTop = chatBody().scrollHeight;
    return m;
  }

  async function onSend(text) {
    text = (text || '').trim();
    if (!text || chat.busy) return;
    chat.busy = true;
    chatSend().disabled = true;
    chatInput().disabled = true;
    const ctx = currentContext();
    pushMsg(esc(text), 'user');
    const typing = pushMsg('<span class="dots"><i></i><i></i><i></i></span> <small style="color:var(--muted)">agent team working…</small>', 'typing');
    const data = await agentAnalyze(text, ctx);
    const stepsHtml = data.steps.length ? `<div class="trace">${data.steps.map((s) => `<span class="t">${esc(s.title)}</span>`).join('')}</div>` : '';
    const agentsHtml = data.agents.length ? `<div class="trace">${data.agents.map((a) => `<span class="t" style="background:var(--green2);color:var(--green)">✧ ${esc(a.name)}</span>`).join('')}</div>` : '';
    const routerHtml = `<div class="trace"><span class="t" style="background:var(--navy);color:#fff">Orchestrator → ${esc(data.routedTo || 'Service Partner')}</span></div>`;
    const dwHtml = data.humanApprovalNeeded ? `<div class="dw-inline">⚠ <b>Human review required</b> — this case is escalated to a banker for approval.</div>` : '';
    typing.outerHTML = `<div class="msg agent">${esc(data.summary)}
      <div class="msg-foot"><span class="conf-pill" style="color:${data.confidence >= 80 ? 'var(--green)' : data.confidence >= 60 ? 'var(--amber)' : 'var(--red)'}">◆ ${data.confidence || 0}% confidence</span><span>${data.evidence.length} evidence · ${data.tools.length} tools · ${data.agents.length} agents</span></div>
      ${routerHtml}${stepsHtml}${agentsHtml}${dwHtml}</div>`;
    chatBody().scrollTop = chatBody().scrollHeight;
    chat.busy = false;
    chatSend().disabled = false;
    chatInput().disabled = false;
    chatInput().value = '';
    chatInput().focus();
  }

  let chatTabEl = null, chatPanelEl = null;
  function openChat(prefill) {
    if (!chatPanelEl) { chatPanelEl = document.getElementById('chatPanel'); chatTabEl = document.getElementById('chatTab'); }
    chatPanelEl.classList.add('open');
    chatTabEl.style.display = 'none';
    syncSuggestions();
    if (prefill) { chatInput().value = prefill; }
    chatInput().focus();
  }

  function initChat() {
    const tab = document.getElementById('chatTab');
    const panel = document.getElementById('chatPanel');
    chatTabEl = tab; chatPanelEl = panel;
    tab.onclick = () => openChat();
    document.getElementById('chatClose').onclick = () => { panel.classList.remove('open'); tab.style.display = ''; };
    chatSend().onclick = () => onSend(chatInput().value);
    chatInput().addEventListener('keydown', (e) => { if (e.key === 'Enter') onSend(chatInput().value); });
    document.getElementById('chatSuggestions').addEventListener('click', (e) => {
      const b = e.target.closest('[data-q]');
      if (b) onSend(b.dataset.q);
    });
  }

  /* ============ render ============ */
  function render() {
    document.querySelectorAll('nav button').forEach((b) => b.classList.toggle('active', b.dataset.page === state.page));
    pages[state.page]();
    addAgentWidget();
  }

  /* ============ events ============ */
  document.querySelectorAll('nav button').forEach((b) => {
    b.onclick = () => { state.page = b.dataset.page; render(); };
  });
  document.querySelector('.menu').onclick = () => document.querySelector('aside').classList.toggle('open');
  document.querySelector('[data-action="newcase"]').onclick = () => { state.page = 'Credit Underwriting'; render(); };

  el.addEventListener('click', (e) => {
    const t = e.target.closest('[data-action]');
    if (!t) return;
    const a = t.dataset.action;
    if (a === 'client') { state.client = +t.dataset.idx; render(); }
    else if (a === 'app') { state.app = +t.dataset.idx; render(); }
    else if (a === 'scenario') { state.scenario = +t.dataset.idx; render(); }
    else if (a === 'alert') { state.alert = +t.dataset.idx; render(); }
    else if (a === 'severity') { state.severity = t.dataset.val; render(); }
    else if (a === 'stress-scenario') { state.stressScenario = +t.dataset.idx; render(); }
    else if (a === 'stress-severity') { state.stressSeverity = +t.dataset.idx; render(); }
  });

  checkBackend().then(() => {
    initChat();
    render();
  });
})();
