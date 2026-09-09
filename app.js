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

  /* ---------- state ---------- */
  const state = { page: 'Overview', client: 0, app: 0, severity: 'All', scenario: 2, alert: 0 };

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

  const pages = { Overview: overview, 'RM Copilot': rmCopilot, 'Credit Underwriting': underwriting, 'Early Warning': earlyWarning, Treasury: treasuryPage, 'Portfolio Risk': portfolioRisk, AML: amlPage };

  function render() {
    document.querySelectorAll('nav button').forEach((b) => b.classList.toggle('active', b.dataset.page === state.page));
    pages[state.page]();
  }

  /* ---------- events ---------- */
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
  });

  render();
})();
