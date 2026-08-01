"""Smoke test for all risk engine modules."""
from config.settings import bank, sectors_cfg, regions_cfg, ratings_cfg
print('✅ config OK')

from data.sample_generator import generate_loan_portfolio, generate_market_data, generate_macro_data, generate_deposit_data
portfolio = generate_loan_portfolio(500)
market = generate_market_data(60)
macro = generate_macro_data(24)
deposits = generate_deposit_data(300)
print(f'✅ data OK — {len(portfolio)} loans, {len(market)} market, {len(macro)} macro, {len(deposits)} deposits')

from risk_engine.credit import compute_credit_metrics, compute_vintage_analysis
credit = compute_credit_metrics(portfolio)
print(f'✅ credit OK — NPL={credit["npl_ratio"]:.2%}, ECL=${credit["total_ecl"]:,.0f}')

from risk_engine.concentration import compute_concentration_metrics
conc = compute_concentration_metrics(portfolio)
print(f'✅ concentration OK — HHI={conc["hhi_borrower"]:.4f}')

from risk_engine.performance import compute_performance_metrics
perf = compute_performance_metrics(credit)
print(f'✅ performance OK — RAROC={perf["raroc"]:.2%}, NIM={perf["nim"]:.2%}')

from risk_engine.market import compute_market_risk_metrics
mkt = compute_market_risk_metrics(market)
print(f'✅ market OK — policy_rate={mkt.get("policy_rate",0):.4f}')

from risk_engine.macro import compute_macro_metrics, compute_portfolio_macro_sensitivity
mc = compute_macro_metrics(macro)
sens = compute_portfolio_macro_sensitivity(credit, mc)
print(f'✅ macro OK — GDP={mc["gdp_growth"]:.2%}, crisis={mc["crisis_probability"]:.1%}')

from risk_engine.liquidity import compute_liquidity_metrics
liq = compute_liquidity_metrics(deposits)
print(f'✅ liquidity OK — LCR={liq["lcr"]:.2%}, NSFR={liq["nsfr"]:.2%}')

from risk_engine.capital import compute_capital_metrics
cap = compute_capital_metrics(credit)
print(f'✅ capital OK — CET1={cap["cet1_ratio"]:.2%}, CAR={cap["total_car"]:.2%}')

from risk_engine.stress import run_all_scenarios, compute_reverse_stress_test
base = {**credit, **cap}
all_scenarios = run_all_scenarios(portfolio, base)
reverse = compute_reverse_stress_test(portfolio, base)
print(f'✅ stress OK — {len(all_scenarios)} scenarios')

from risk_engine.ai_models import train_default_prediction_model, detect_anomalies, compute_risk_drivers, generate_ai_alerts
model = train_default_prediction_model(portfolio)
anomalies = detect_anomalies(portfolio)
drivers = compute_risk_drivers(portfolio)
alerts = generate_ai_alerts(anomalies, model)
print(f'✅ AI OK — AUC={model.get("auc","N/A"):.3f}, anomalies={anomalies["is_anomaly"].sum()}, alerts={len(alerts)}')

print()
print('🎉 ALL MODULES IMPORTED AND TESTED SUCCESSFULLY')
