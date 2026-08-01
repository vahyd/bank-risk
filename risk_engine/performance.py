"""
Risk-Adjusted Performance Engine.
Computes RAROC, NIM, ROA, ROE, cost of credit risk, and economic capital usage.
"""
from config.settings import bank


def compute_performance_metrics(portfolio_metrics: dict, bank_cfg=None) -> dict:
    """Compute risk-adjusted performance metrics."""

    if bank_cfg is None:
        bank_cfg = bank

    # Extract from bank config
    interest_income = bank_cfg.interest_income
    interest_expense = bank_cfg.interest_expense
    operating_cost = bank_cfg.operating_cost
    credit_losses = bank_cfg.credit_losses
    net_income = bank_cfg.net_income
    total_assets = bank_cfg.total_assets
    total_equity = bank_cfg.total_equity
    total_loans = portfolio_metrics.get("total_portfolio", bank_cfg.total_loans)

    # Net Interest Margin (NIM)
    earning_assets = total_loans * 0.90  # approx earning assets
    nim = (interest_income - interest_expense) / earning_assets if earning_assets > 0 else 0

    # Cost of Credit Risk
    cost_of_credit = credit_losses / total_loans if total_loans > 0 else 0

    # Return on Assets (ROA)
    roa = net_income / total_assets if total_assets > 0 else 0

    # Return on Equity (ROE)
    roe = net_income / total_equity if total_equity > 0 else 0

    # Risk-Adjusted Return on Capital (RAROC)
    risk_adjusted_income = interest_income - interest_expense - operating_cost - credit_losses
    economic_capital = portfolio_metrics.get("total_ul", total_loans * 0.05)
    raroc = risk_adjusted_income / economic_capital if economic_capital > 0 else 0

    # Economic Capital Usage
    total_ecl = portfolio_metrics.get("total_ecl", credit_losses)
    total_ul = portfolio_metrics.get("total_ul", total_loans * 0.05)
    ecap_usage_pct = economic_capital / total_equity if total_equity > 0 else 0

    # Income breakdown
    gross_interest_margin = interest_income - interest_expense
    pre_provision_profit = gross_interest_margin - operating_cost
    post_provision_profit = pre_provision_profit - credit_losses

    return {
        "interest_income": interest_income,
        "interest_expense": interest_expense,
        "gross_interest_margin": gross_interest_margin,
        "operating_cost": operating_cost,
        "pre_provision_profit": pre_provision_profit,
        "credit_losses": credit_losses,
        "post_provision_profit": post_provision_profit,
        "net_income": net_income,
        "nim": nim,
        "cost_of_credit": cost_of_credit,
        "roa": roa,
        "roe": roe,
        "raroc": raroc,
        "economic_capital": economic_capital,
        "economic_capital_usage_pct": ecap_usage_pct,
        "risk_adjusted_income": risk_adjusted_income,
        "earning_assets": earning_assets,
    }
