"""Basic health check tests."""
import pytest
from httpx import ASGITransport, AsyncClient

from telegram_scraper.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test health endpoint returns OK."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_api_v1_available(client: AsyncClient):
    """Test API v1 router is available."""
    response = await client.get("/api/v1/auth/me")
    # Should get 401 unauthorized (not 404), meaning the endpoint exists
    assert response.status_code == 401
