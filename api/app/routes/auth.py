"""
Auth API Router
The FOB Platform

Endpoints:
  POST /api/v1/auth/enter   - Email entry gate (upsert user, return token)
  GET  /api/v1/auth/verify  - Verify a token (Bearer header)
"""

import re
import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class EnterRequest(BaseModel):
    email: str


async def _get_session(request: Request) -> AsyncSession:
    """Get a DB session from the app state."""
    try:
        factory = request.app.state.session_factory
        return factory()
    except AttributeError:
        raise HTTPException(
            status_code=503,
            detail="Database not available",
        )


@router.post("/enter", summary="Email entry gate")
async def enter(body: EnterRequest, request: Request):
    """
    Accept an email, upsert the user, and return a token (user UUID).
    If the email already exists, update last_login.
    If new, create a new user record.
    """
    email = body.email.strip().lower()

    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="Invalid email format")

    session = await _get_session(request)
    async with session:
        # Check if user already exists
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Update last_login
            user.last_login = datetime.utcnow()
            await session.commit()
            logger.info("Returning user", extra={"email": email})
        else:
            # Create new user
            user = User(
                id=str(uuid.uuid4()),
                email=email,
            )
            session.add(user)
            await session.commit()
            logger.info("New user created", extra={"email": email})

        return {
            "user_id": user.id,
            "token": user.id,
            "email": user.email,
        }


@router.get("/verify", summary="Verify auth token")
async def verify(request: Request):
    """
    Verify a Bearer token (user UUID). Returns user info or 401.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    session = await _get_session(request)
    async with session:
        stmt = select(User).where(User.id == token)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        return {
            "valid": True,
            "user_id": user.id,
            "email": user.email,
        }
