"""Retrieval layer for the Relationship Manager assistant.

Builds a per-customer text corpus (profile, transactions, risk, alerts,
policies), indexes it with TF-IDF (scikit-learn), retrieves the most relevant
documents for a query, and passes them to the LLM (Ollama / fallback).

A production deployment can swap this for a vector database (pgvector/Qdrant)
and Haystack pipelines — the interface stays the same.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..db import Alert, CreditFacility, Customer, SessionLocal, Transaction
from ..ml.llm import generate_with_sources

SYSTEM_PROMPT = (
    "You are the Relationship Manager copilot inside a corporate banking platform. "
    "Answer concisely using only the provided context. Cite document numbers. "
    "Never invent figures. If data is missing, say so. Never make final credit decisions."
)


def build_corpus(db) -> list[dict]:
    """One document per customer plus policy documents."""
    docs: list[dict] = []
    customers = db.query(Customer).all()
    for c in customers:
        facilities = db.query(CreditFacility).filter(CreditFacility.customer_id == c.id).all()
        alerts = db.query(Alert).filter(Alert.customer_id == c.id).all()
        tx_count = db.query(Transaction).filter(Transaction.customer_id == c.id).count()
        fac_txt = "; ".join(
            f"{f.facility_type} limit {f.limit_amount:,.0f} {f.currency} util {f.utilization:.0%} grade {f.risk_grade}"
            for f in facilities
        ) or "no credit facilities"
        alert_txt = "; ".join(f"{a.app} {a.severity} {a.title}" for a in alerts[:5]) or "no open alerts"
        text = (
            f"Customer {c.legal_name} ({c.registration_number}). Industry: {c.industry}. "
            f"Country: {c.country}. Size: {c.size}. Annual turnover: {c.annual_turnover:,.0f}. "
            f"Employees: {c.employees}. Group: {c.group_id}. RM: {c.rm_name}. "
            f"KYC: {c.kyc_status}. Sanctioned: {c.sanctioned}. PEP: {c.pep}. "
            f"Products: {', '.join(c.products)}. "
            f"Credit: {fac_txt}. Alerts: {alert_txt}. Transactions recorded: {tx_count}. "
            f"Operating countries: {', '.join(c.operating_countries)}."
        )
        docs.append({"text": text, "source": f"customer:{c.id}", "customer_id": c.id,
                     "title": c.legal_name})
    docs.extend([
        {"text": "Policy: loans are never auto-approved; every elevated-risk decision requires human "
                 "approval in the Dual Workforce checkpoint.", "source": "policy:approval",
         "customer_id": None, "title": "Approval Policy"},
        {"text": "Policy: AML reporting threshold is 10,000 currency units; transactions just below "
                 "this threshold are flagged for structuring review.", "source": "policy:aml",
         "customer_id": None, "title": "AML Policy"},
        {"text": "Policy: covenant breach (DSCR < 1.25x or Debt/EBITDA > 4.0x) moves the customer to "
                 "watchlist and requires relationship-manager review.", "source": "policy:covenants",
         "customer_id": None, "title": "Covenant Policy"},
    ])
    return docs


class RAGIndex:
    def __init__(self) -> None:
        self.docs: list[dict] = []
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=4000)
        self.matrix = None

    def build(self, docs: list[dict]) -> None:
        self.docs = docs
        self.matrix = self.vectorizer.fit_transform([d["text"] for d in docs])

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        if self.matrix is None or self.matrix.shape[0] == 0:
            return []
        q = self.vectorizer.transform([query])
        sims = cosine_similarity(q, self.matrix)[0]
        idx = np.argsort(sims)[::-1][:top_k]
        return [self.docs[int(i)] for i in idx if sims[i] > 0.01]


rag_index = RAGIndex()


def answer_rm_question(query: str, customer_id: int | None = None) -> dict:
    db = SessionLocal()
    try:
        docs = build_corpus(db)
        rag_index.build(docs)
        if customer_id is not None:
            scoped = [d for d in docs if d.get("customer_id") == customer_id]
            # still allow policy docs
            scoped += [d for d in docs if d.get("customer_id") is None]
            hits = rag_index.search(query, top_k=6)
            hits = [h for h in hits if (h.get("customer_id") in (None, customer_id))]
            hits = hits[:4] or scoped[:3]
        else:
            hits = rag_index.search(query, top_k=4)

        result = generate_with_sources(SYSTEM_PROMPT, query, hits)
        result["retrieved"] = [{"title": h["title"], "source": h["source"],
                                "customer_id": h.get("customer_id")} for h in hits]
        # extract a deterministic snippet when the LLM is in fallback mode
        if result["provider"] == "fallback":
            result["extractive_answer"] = _extractive(query, hits)
        return result
    finally:
        db.close()


def _extractive(query: str, hits: list[dict]) -> str:
    q = query.lower()
    lines: list[str] = []
    for h in hits:
        sentences = re.split(r"(?<=[.;]) ", h["text"])
        for s in sentences:
            words = set(re.findall(r"\w+", q))
            if any(w.lower() in s.lower() for w in words) and s not in lines:
                lines.append(s)
        if len(lines) >= 4:
            break
    if not lines:
        return "No specific match found in retrieved records. Try asking about a customer, exposure, or policy."
    return " · ".join(lines[:4])
