"""Audit logging helper — every consequential action is recorded."""
from __future__ import annotations

from .db import AuditLog, SessionLocal, jsonable


def log(user: str, role: str, action: str, resource: str, detail: dict | None = None) -> None:
    db = SessionLocal()
    try:
        db.add(AuditLog(user=user, role=role, action=action, resource=resource, detail=jsonable(detail or {})))
        db.commit()
    finally:
        db.close()
