import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ENDPOINTS_GET = [
    "/api/v1/career/roles",
    "/api/v1/career/certifications",
    "/api/v1/career/targets",
    "/api/v1/programs",
    "/api/v1/programs/map",
    "/api/v1/programs/stats",
    "/api/v1/communities",
    "/api/v1/ergs",
    "/api/v1/news",
]

@pytest.mark.parametrize("endpoint", ENDPOINTS_GET)
def test_get_endpoints(endpoint):
    response = client.get(endpoint)
    # We expect either 200 OK or 503 Service Unavailable (if DB not present)
    # We do not expect 500 Internal Server Error
    assert response.status_code in (200, 503), f"Endpoint {endpoint} returned {response.status_code}"

ENDPOINTS_POST = [
    ("/api/v1/roadmap/generate", {"target_role": "Cybersecurity", "user_background": "Infantry"}),
    ("/api/v1/networking/analyze", {"linkedin_url": "https://linkedin.com/in/test"}),
    ("/api/v1/networking/roadmap", {"target_industry": "Tech"}),
]

@pytest.mark.parametrize("endpoint,payload", ENDPOINTS_POST)
def test_post_endpoints(endpoint, payload):
    response = client.post(endpoint, json=payload)
    # 401 Unauthorized might happen if route requires auth, 422 for validation, 503 for DB
    assert response.status_code not in (500,), f"Endpoint {endpoint} returned 500 Internal Server Error"

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()
