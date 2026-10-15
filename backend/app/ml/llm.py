"""Open-source LLM integration via Ollama (Llama 3.1 / Mistral) with a deterministic
fallback so the platform works without any external service or GPU.

Production deployments can point OLLAMA_URL at a self-hosted Ollama instance.
"""
from __future__ import annotations

import json

import httpx

from ..config import settings


def ollama_available() -> bool:
    try:
        r = httpx.get(f"{settings.ollama_url}/api/tags", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


def generate(system: str, prompt: str, context: str | None = None) -> dict:
    """Generate text via Ollama; falls back to a deterministic extractive answer."""
    full_prompt = prompt
    if context:
        full_prompt = f"Use ONLY the following context to answer. If the answer is not in the context, say so.\n\nCONTEXT:\n{context}\n\nQUESTION:\n{prompt}"

    if settings.llm_fallback and ollama_available():
        try:
            r = httpx.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": settings.ollama_model, "system": system,
                      "prompt": full_prompt, "stream": False,
                      "options": {"temperature": 0.2, "num_predict": 1024}},
                timeout=settings.ollama_timeout_s,
            )
            r.raise_for_status()
            data = r.json()
            return {
                "answer": data.get("response", "").strip(),
                "model": settings.ollama_model,
                "provider": "ollama",
                "sources": [],
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "answer": f"(Ollama call failed: {exc}) — showing fallback answer. "
                          "Install Ollama and pull a model to enable open-source LLM answers.",
                "model": settings.ollama_model,
                "provider": "fallback",
                "sources": [],
            }

    return {
        "answer": "Open-source LLM not reachable. Start Ollama (`ollama serve`) and pull a model "
                  f"(e.g. `ollama pull {settings.ollama_model}`) to enable generative answers. "
                  "The extractive answer below is computed locally from retrieved records.",
        "model": settings.ollama_model,
        "provider": "fallback",
        "sources": [],
    }


def generate_with_sources(system: str, prompt: str, context_docs: list[dict]) -> dict:
    """RAG generation: retrieve-and-generate with citation tracking."""
    context = "\n\n".join(f"[{i+1}] {d['text']}" for i, d in enumerate(context_docs))
    result = generate(system, prompt, context)
    result["sources"] = [d["source"] for d in context_docs]
    return result


def chat(messages: list[dict]) -> dict:
    """Simple multi-turn chat via Ollama /api/chat, with fallback."""
    if settings.llm_fallback and ollama_available():
        try:
            r = httpx.post(
                f"{settings.ollama_url}/api/chat",
                json={"model": settings.ollama_model, "messages": messages,
                      "stream": False, "options": {"temperature": 0.3}},
                timeout=settings.ollama_timeout_s,
            )
            r.raise_for_status()
            data = r.json()
            return {"answer": data.get("message", {}).get("content", "").strip(),
                    "model": settings.ollama_model, "provider": "ollama"}
        except Exception:
            pass
    return {"answer": "LLM unavailable — chat fallback active. Run Ollama to enable conversational answers.",
            "model": settings.ollama_model, "provider": "fallback"}
