import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_login_success(client: AsyncClient):
    resp = await client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "ADMIN"
    assert data["username"] == "admin"


async def test_login_wrong_password(client: AsyncClient):
    resp = await client.post("/auth/login", data={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


async def test_login_unknown_user(client: AsyncClient):
    resp = await client.post("/auth/login", data={"username": "nobody", "password": "x"})
    assert resp.status_code == 401


async def test_token_grants_access(client: AsyncClient):
    resp = await client.post("/auth/login", data={"username": "analyst1", "password": "analyst123"})
    token = resp.json()["access_token"]
    me_resp = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "analyst1"


async def test_invalid_token_rejected(client: AsyncClient):
    resp = await client.get("/users/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401
