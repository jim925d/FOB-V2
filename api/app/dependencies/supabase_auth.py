"""
Verify Supabase JWT from Authorization header.
Use on endpoints that need the authenticated user (e.g. ERG submit).
SECURITY: SUPABASE_JWT_SECRET is server-side only; never expose to frontend.
"""
from uuid import UUID

from fastapi import Request, HTTPException
from jose import jwt, JWTError

from app.config import get_settings


def _get_bearer_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        return None
    return auth[7:].strip() or None


async def get_user_id_from_request(request: Request) -> UUID:
    """
    Resolve user id from request:
    - If Supabase is configured: verify JWT and return sub (user id).
    - Else: treat Bearer token as legacy user UUID (backward compat).
    """
    token = _get_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Sign in to submit your company's veteran ERG")

    settings = get_settings()
    if settings.supabase_jwt_secret:
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_aud": True},
            )
            sub = payload.get("sub")
            if not sub:
                raise HTTPException(status_code=401, detail="Invalid token")
            return UUID(sub)
        except JWTError:
            try:
                payload = jwt.decode(
                    token,
                    settings.supabase_jwt_secret,
                    algorithms=["HS256"],
                )
                sub = payload.get("sub")
                if not sub:
                    raise HTTPException(status_code=401, detail="Invalid token")
                return UUID(sub)
            except JWTError:
                raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Legacy: Bearer token is the user UUID (from old auth/enter)
    try:
        return UUID(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
