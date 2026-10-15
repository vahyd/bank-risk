"""Central configuration. All values can be overridden via environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Corporate Banking AI Platform"
    version: str = "2.0.0"
    environment: str = "development"  # development | testing | production

    # Database — PostgreSQL in production, SQLite fallback for zero-dependency local dev.
    database_url: str = "sqlite:///./data/app.db"

    # Data & model artifacts
    data_dir: str = "../data"          # relative to backend/ working dir
    artifacts_dir: str = "../data/models"

    # Synthetic data generation
    n_customers: int = 120
    n_accounts: int = 260
    n_transactions: int = 28_000
    n_facilities: int = 110
    seed: int = 42

    # LLM — open-source models served by Ollama (Llama 3.1 / Mistral).
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"     # or "mistral", "llama3.1:8b", ...
    ollama_timeout_s: float = 120.0
    llm_fallback: bool = True          # deterministic extractive answers when Ollama is absent

    # Risk thresholds (configurable, jurisdiction-specific)
    aml_reporting_threshold: float = 10_000.0
    fraud_alert_threshold: float = 0.75
    aml_alert_threshold: float = 0.70
    large_txn_threshold: float = 250_000.0

    # API
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    # Resolve artifact paths relative to backend/ so they work from any cwd.
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for attr in ("data_dir", "artifacts_dir"):
        val = getattr(s, attr)
        if not os.path.isabs(val):
            setattr(s, attr, os.path.normpath(os.path.join(backend_dir, val)))
    return s


settings = get_settings()
