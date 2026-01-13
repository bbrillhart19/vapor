from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from vapor.app import routes


### Status routes ###
async def test_health_check():
    """Tests the /status/health endpoint"""
    app = FastAPI()
    app.include_router(routes.status_router)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/status/health")

    assert response.json() == {"status": "alive"}
    assert response.status_code == 200
