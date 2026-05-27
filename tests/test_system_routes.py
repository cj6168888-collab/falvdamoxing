import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.system import router


@pytest.fixture
async def client():
    app = FastAPI()
    app.include_router(router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.asyncio
async def test_system_health_route(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_system_root_route(client):
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "法律大模型辅助系统 API"
    assert data["status"] == "running"
    assert "version" in data
