"""Transaction-network analysis with NetworkX (fraud chains, AML circular flows)."""
from __future__ import annotations

import networkx as nx
import pandas as pd


def build_graph(transactions: pd.DataFrame, iban_to_id: dict[str, int] | None = None) -> nx.DiGraph:
    """Build a directed account graph. When a counterparty account is an IBAN of an
    internal account, it is mapped back to the account id so chains connect."""
    iban_to_id = iban_to_id or {}
    g = nx.DiGraph()
    for _, t in transactions.iterrows():
        src = t["account_id"]
        dst = t["counterparty_account"]
        if src == dst or pd.isna(dst):
            continue
        dst_id = iban_to_id.get(str(dst), dst)
        if not g.has_node(src):
            g.add_node(src, internal=True)
        if not g.has_node(dst_id):
            g.add_node(dst_id, internal=bool(t.get("is_internal", False)) or dst_id in iban_to_id.values())
        g.add_edge(src, dst_id, amount=t["amount"], txn_id=t["id"], timestamp=t["timestamp"])
    return g


def circular_flows(transactions: pd.DataFrame, min_amount: float = 50_000.0,
                   iban_to_id: dict[str, int] | None = None) -> list[dict]:
    """Find closed loops of transfers (A->B->...->A) within the internal network."""
    internal = transactions[transactions["is_internal"] == True]  # noqa: E712
    if len(internal) < 3:
        return []
    g = build_graph(internal, iban_to_id)
    found: list[dict] = []
    for cycle in nx.simple_cycles(g):
        if len(cycle) < 3 or len(cycle) > 6:
            continue
        amounts = []
        txns = []
        ok = True
        for i, node in enumerate(cycle):
            nxt = cycle[(i + 1) % len(cycle)]
            best = None
            for _, _, data in g.out_edges(node, data=True):
                if data["txn_id"] in [t["txn_id"] for t in txns]:
                    continue
                if data["amount"] >= min_amount:
                    best = data
                    break
            if best is None:
                ok = False
                break
            amounts.append(best["amount"])
            txns.append(best)
        if ok and len(txns) >= 3:
            found.append({
                "accounts": cycle,
                "txn_ids": [t["txn_id"] for t in txns],
                "total_amount": round(float(sum(amounts)), 2),
                "pattern": "circular_transfer",
            })
        if len(found) >= 20:
            break
    return found


def rapid_movement(transactions: pd.DataFrame, within_hours: int = 48,
                   ratio: float = 0.8, min_amount: float = 100_000.0) -> list[dict]:
    """Inflow immediately followed by similar-sized outflow (layering indicator)."""
    t = transactions.sort_values(["account_id", "timestamp"])
    found: list[dict] = []
    for acct, grp in t.groupby("account_id"):
        grp = grp.reset_index(drop=True)
        for i in range(len(grp) - 1):
            a, b = grp.iloc[i], grp.iloc[i + 1]
            if a["direction"] == "credit" and b["direction"] == "debit":
                dt = (b["timestamp"] - a["timestamp"]).total_seconds() / 3600.0
                if dt <= within_hours and a["amount"] >= min_amount and b["amount"] >= ratio * a["amount"]:
                    found.append({
                        "account_id": int(acct),
                        "txn_in": int(a["id"]),
                        "txn_out": int(b["id"]),
                        "amount_in": round(float(a["amount"]), 2),
                        "amount_out": round(float(b["amount"]), 2),
                        "hours_between": round(dt, 1),
                        "pattern": "rapid_movement",
                    })
    return found[:50]


def shared_counterparty_clusters(transactions: pd.DataFrame, min_companies: int = 3) -> list[dict]:
    """Groups of companies transacting with the same external counterparties."""
    t = transactions[transactions["is_internal"] == False]  # noqa: E712
    pairs = t.groupby("counterparty_account")["customer_id"].apply(lambda s: sorted(set(s.tolist())))
    clusters: dict[tuple, set[str]] = {}
    for cp, custs in pairs.items():
        key = tuple(sorted(custs))
        if len(key) >= min_companies:
            clusters.setdefault(key, set()).add(cp)
    return [{"customers": list(k), "shared_counterparties": sorted(v)} for k, v in clusters.items()][:30]
