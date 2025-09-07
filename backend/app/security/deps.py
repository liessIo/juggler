# backend/app/security/deps.py
import os
import hmac
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Optional JWT support
try:
    from jose import JWTError, jwt  # python-jose
except Exception:
    JWTError = Exception  # type: ignore
    jwt = None  # type: ignore

_auth_scheme = HTTPBearer(auto_error=False)

def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if v is not None else default

def _is_probably_jwt(token: str) -> bool:
    # crude but safe-enough heuristic: JWTs have 3 dot-separated parts
    return token.count(".") == 2

def require_auth(credentials: HTTPAuthorizationCredentials = Depends(_auth_scheme)) -> str:
    """
    Accept either:
      - Self-hosted static bearer token via JUGGLER_API_TOKEN, or
      - JWT (if JWT_SECRET is set; HS algorithms by default).
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = credentials.credentials
    static_token = _env("JUGGLER_API_TOKEN")

    # 1) If a static token is configured, prefer constant-time comparison
    if static_token:
        if not hmac.compare_digest(token, static_token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return token

    # 2) Otherwise, accept JWT if configured
    jwt_secret = _env("JWT_SECRET")
    jwt_alg = _env("JWT_ALGORITHM", "HS256")
    if jwt_secret and jwt and _is_probably_jwt(token):
        try:
            jwt.decode(token, jwt_secret, algorithms=[jwt_alg])
            return token
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT")

    # 3) If neither is configured, fail-fast (secure-by-default)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Server misconfigured: set JUGGLER_API_TOKEN or JWT_SECRET",
    )