"""Lightweight RBAC for demo/prototype use.

Production deployment should replace this with OIDC/SAML + short-lived tokens.
For the prototype we accept an `X-User` + `X-Role` header pair (or a local
`Authorization: Bearer <role>:<user>` token) and enforce role permissions.
"""
from __future__ import annotations

import functools
from typing import Callable

from fastapi import Header, HTTPException, Request

ROLES = ("admin", "analyst", "rm", "compliance", "treasury")

# role -> allowed actions. "*" means everything.
PERMISSIONS: dict[str, set[str]] = {
    "admin": {"*"},
    "analyst": {"dashboard:read", "credit:read", "fraud:read", "fraud:write", "aml:read",
               "liquidity:read", "segmentation:read", "models:read", "customers:read"},
    "rm": {"dashboard:read", "customers:read", "rm:read", "rm:write", "credit:read",
           "liquidity:read", "segmentation:read"},
    "compliance": {"dashboard:read", "aml:read", "aml:write", "customers:read", "audit:read"},
    "treasury": {"dashboard:read", "liquidity:read", "liquidity:write", "customers:read"},
}

DEFAULT_ROLE = "admin"


def current_identity(request: Request) -> tuple[str, str]:
    """Return (username, role) from headers with a permissive prototype default."""
    user = request.headers.get("X-User", request.headers.get("x-user", "demo-user"))
    role = request.headers.get("X-Role", request.headers.get("x-role", DEFAULT_ROLE))
    if role not in ROLES:
        raise HTTPException(status_code=403, detail=f"Unknown role '{role}'")
    return user, role


def require(action: str) -> Callable:
    """FastAPI dependency enforcing `action` permission."""
    def dependency(request: Request) -> tuple[str, str]:
        user, role = current_identity(request)
        allowed = PERMISSIONS.get(role, set())
        if "*" not in allowed and action not in allowed:
            raise HTTPException(status_code=403, detail=f"Role '{role}' cannot perform '{action}'")
        return user, role
    return dependency


def has_permission(role: str, action: str) -> bool:
    allowed = PERMISSIONS.get(role, set())
    return "*" in allowed or action in allowed
