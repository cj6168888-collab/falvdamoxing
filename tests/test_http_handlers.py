import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from app.core.http_handlers import configure_http_handlers


@pytest.mark.asyncio
async def test_http_handlers_add_utf8_charset_to_json_responses():
    app = FastAPI()
    configure_http_handlers(app)

    @app.get("/json")
    def json_endpoint():
        return JSONResponse({"status": "ok"})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/json")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json; charset=utf-8"
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_http_handlers_return_json_for_uncaught_exceptions():
    app = FastAPI()
    configure_http_handlers(app)

    @app.get("/boom")
    def boom():
        raise ValueError("bad input")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/boom")

    assert response.status_code == 500
    assert response.headers["content-type"] == "application/json; charset=utf-8"
    assert response.json() == {
        "detail": "服务器内部错误: bad input",
        "type": "ValueError",
    }
