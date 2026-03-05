"""
Integration tests for authentication and user management endpoints.
Uses httpx.AsyncClient against a real test database.

To run:
    pytest tests/ -v --asyncio-mode=auto
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

BASE = "/api/v1"


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ──────────────── Health ──────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ──────────────── Registration ───────────────────────────

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    payload = {
        "username": "testuser1",
        "email": "testuser1@example.com",
        "password": "TestPass123",
    }
    resp = await client.post(f"{BASE}/users/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == payload["email"]
    assert data["role"] == "user"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "username": "uniqueuser",
        "email": "dup@example.com",
        "password": "TestPass123",
    }
    await client.post(f"{BASE}/users/register", json=payload)
    resp = await client.post(
        f"{BASE}/users/register",
        json={**payload, "username": "anotheruser"},
    )
    assert resp.status_code == 409


# ──────────────── Login ───────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post(
        f"{BASE}/users/register",
        json={"username": "logintest", "email": "login@example.com", "password": "TestPass123"},
    )
    resp = await client.post(
        f"{BASE}/auth/login",
        json={"email": "login@example.com", "password": "TestPass123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert "refresh_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    resp = await client.post(
        f"{BASE}/auth/login",
        json={"email": "login@example.com", "password": "WrongPass999"},
    )
    assert resp.status_code == 401


# ──────────────── Protected Routes ───────────────────────

@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    await client.post(
        f"{BASE}/users/register",
        json={"username": "meuser", "email": "me@example.com", "password": "TestPass123"},
    )
    login_resp = await client.post(
        f"{BASE}/auth/login",
        json={"email": "me@example.com", "password": "TestPass123"},
    )
    token = login_resp.json()["access_token"]

    resp = await client.get(
        f"{BASE}/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    resp = await client.get(f"{BASE}/users/me")
    assert resp.status_code == 401
