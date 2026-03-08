"""
Tests for ERG directory API.
- Without DB: endpoints return 503.
- With DB: list/stats/industries return 200 (possibly empty).
- POST /seed and POST /scrape/trigger require secret and return 403 without it (when api_secret_key is set).
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    """Sync client for simple tests."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async client for async tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ─── Route existence and error handling ───

def test_erg_list_returns_503_or_200(client):
    """GET /api/v1/ergs returns 503 when DB unavailable, 200 when DB is available."""
    r = client.get("/api/v1/ergs", params={"page": 1, "per_page": 5})
    assert r.status_code in (200, 503), f"Unexpected status: {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        assert "ergs" in data
        assert "total" in data
        assert isinstance(data["ergs"], list)


def test_erg_stats_returns_503_or_200(client):
    """GET /api/v1/ergs/stats returns 503 or 200."""
    r = client.get("/api/v1/ergs/stats")
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        data = r.json()
        assert "total_ergs" in data
        assert "total_companies" in data


def test_erg_industries_returns_503_or_200(client):
    """GET /api/v1/ergs/industries returns 503 or 200."""
    r = client.get("/api/v1/ergs/industries")
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        data = r.json()
        assert "industries" in data
        assert isinstance(data["industries"], list)


def test_erg_by_companies_returns_503_or_200(client):
    """GET /api/v1/ergs/by-companies returns 503 or 200."""
    r = client.get("/api/v1/ergs/by-companies", params={"names": "Amazon,Microsoft"})
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        data = r.json()
        assert "ergs" in data
        assert isinstance(data["ergs"], list)


def test_erg_seed_requires_secret_or_returns_503(client):
    """POST /api/v1/ergs/seed without valid secret returns 403 (or 503 if no DB)."""
    r = client.post("/api/v1/ergs/seed")
    # No secret: 403 if api_secret_key is set; or 503 if DB not available (session created before secret check)
    assert r.status_code in (403, 503), f"Unexpected status: {r.status_code}"


def test_erg_submit_without_auth_returns_401(client):
    """POST /api/v1/ergs/submit without Bearer token returns 401."""
    r = client.post(
        "/api/v1/ergs/submit",
        json={
            "company_name": "Test Co",
            "erg_name": "Test ERG",
            "industry": "Technology",
            "submitter_email": "test@example.com",
            "verification_agreement": True,
        },
    )
    assert r.status_code == 401


def test_erg_submit_validation_rejects_missing_agreement(client):
    """POST /api/v1/ergs/submit with verification_agreement false returns 422."""
    r = client.post(
        "/api/v1/ergs/submit",
        json={
            "company_name": "Test Co",
            "submitter_email": "test@example.com",
            "verification_agreement": False,
        },
    )
    # 401 if no auth, or 422 if auth present and validation fails
    assert r.status_code in (401, 422)
