import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _login(client: AsyncClient, username: str) -> str:
    password = "admin123" if username == "admin" else "analyst123"
    resp = await client.post("/auth/login", data={"username": username, "password": password})
    return resp.json()["access_token"]


async def test_create_chat_session(client: AsyncClient):
    token = await _login(client, "analyst1")
    resp = await client.post(
        "/chat/sessions",
        json={"title": "Test session"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test session"
    assert "id" in data


async def test_list_chat_sessions(client: AsyncClient):
    token = await _login(client, "analyst1")
    await client.post(
        "/chat/sessions",
        json={"title": "Session 1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get("/chat/sessions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_send_message_and_get_response(client: AsyncClient):
    token = await _login(client, "analyst1")
    sess_resp = await client.post(
        "/chat/sessions",
        json={"title": "Chat test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    session_id = sess_resp.json()["id"]

    msg_resp = await client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "What incidents are there?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert msg_resp.status_code == 201
    data = msg_resp.json()
    assert data["role"] == "ASSISTANT"
    assert "content" in data


async def test_get_messages(client: AsyncClient):
    token = await _login(client, "analyst1")
    sess_resp = await client.post(
        "/chat/sessions",
        json={"title": "Msg test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    session_id = sess_resp.json()["id"]

    await client.post(
        f"/chat/sessions/{session_id}/messages",
        json={"content": "Hello"},
        headers={"Authorization": f"Bearer {token}"},
    )

    get_resp = await client.get(
        f"/chat/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    messages = get_resp.json()
    assert len(messages) >= 1  # At least the AI response
