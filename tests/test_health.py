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
async def test_root_redirects_to_docs(client: AsyncClient):
    """Test root endpoint redirects to docs."""
    response = await client.get("/", follow_redirects=False)
    assert response.status_code in [307, 308, 302, 301]
