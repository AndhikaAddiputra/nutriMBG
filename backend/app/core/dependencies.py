"""
core/dependencies.py
====================
Reusable FastAPI dependencies for authentication and authorisation.

JWT format expected
-------------------
Header : Authorization: Bearer <token>
Payload: { "sub": "<user_id>", "role": "<role>", "exp": <unix_ts> }

Roles
-----
  "admin"       – full access to /api/admin/* endpoints
  "coordinator" – standard user; blocked from admin endpoints
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel

from app.core.settings import settings

# ---------------------------------------------------------------------------
# Scheme
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=True)


# ---------------------------------------------------------------------------
# Token payload model
# ---------------------------------------------------------------------------


class TokenPayload(BaseModel):
    sub: str
    role: str = "coordinator"


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT; raise HTTP 401 on any failure."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
        return TokenPayload(sub=str(payload["sub"]), role=payload.get("role", "coordinator"))
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sudah kadaluarsa.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (JWTError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# Public dependencies
# ---------------------------------------------------------------------------


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
) -> TokenPayload:
    """Validate JWT and return the token payload."""
    return _decode_token(credentials.credentials)


def require_admin(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
) -> TokenPayload:
    """
    Require the caller to have role='admin'.
    Raises HTTP 403 Forbidden for any other role.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Endpoint ini hanya untuk administrator.",
        )
    return current_user