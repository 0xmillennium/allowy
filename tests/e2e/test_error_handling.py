from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import SQLAlchemyError

from src.core.exceptions.handlers import EXCEPTION_HANDLERS
from src.entrypoints.http.dependencies import get_uow
from src.entrypoints.http.ip_sources import router as ip_sources_router


class _FailingUoW:
    """A UoW stub that raises on context entry."""

    def __init__(self, exc: Exception):
        self._exc = exc

    async def __aenter__(self):
        raise self._exc

    async def __aexit__(self, *args):
        pass


def _make_app(uow_override) -> FastAPI:
    app = FastAPI()
    app.include_router(ip_sources_router)
    for exc_class, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exc_class, handler)
    app.dependency_overrides[get_uow] = lambda: uow_override
    return app


def _make_transport(app: FastAPI, raise_app_exceptions: bool = True) -> ASGITransport:
    return ASGITransport(app=app, raise_app_exceptions=raise_app_exceptions)


class TestSQLAlchemyErrorHandler:
    async def test_database_error_returns_500(self):
        app = _make_app(_FailingUoW(SQLAlchemyError("connection lost")))
        transport = _make_transport(app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ip-sources")
        assert response.status_code == 500
        data = response.json()
        assert data["code"] == 500
        assert data["type"] == "database_error"
        assert "database error" in data["msg"].lower()


class TestGenericErrorHandler:
    async def test_unexpected_error_returns_500(self):
        app = _make_app(_FailingUoW(RuntimeError("unexpected failure")))
        transport = _make_transport(app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ip-sources")
        assert response.status_code == 500
        data = response.json()
        assert data["code"] == 500
        assert data["type"] == "internal_error"
        assert "unexpected error" in data["msg"].lower()
