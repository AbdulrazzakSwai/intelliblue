import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _login(client: AsyncClient, username: str, password: str = "analyst123") -> str:
    if username == "admin":
        password = "admin123"
    resp = await client.post("/auth/login", data={"username": username, "password": password})
    return resp.json()["access_token"]


async def test_admin_can_list_users(client: AsyncClient):
    token = await _login(client, "admin")
    resp = await client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 3


async def test_l1_cannot_list_users(client: AsyncClient):
    token = await _login(client, "analyst1")
    resp = await client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


async def test_l2_cannot_list_users(client: AsyncClient):
    token = await _login(client, "analyst2")
    resp = await client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


async def test_l1_cannot_close_incident(client: AsyncClient, db_session):
    """L1 calling close endpoint should get 403."""
    import uuid
    from app.models.incident import Incident, IncidentStatus, IncidentSeverity
    from app.models.dataset import Dataset, DatasetStatus

    # Create a dataset and incident directly
    ds = Dataset(
        id=str(uuid.uuid4()),
        name="test",
        status=DatasetStatus.READY.value,
        uploaded_by=list((await db_session.execute(
            __import__('sqlalchemy').select(__import__('app.models.user', fromlist=['User']).User)
            .where(__import__('app.models.user', fromlist=['User']).User.username == 'analyst1')
        )).scalars())[0].id,
        event_count=0,
        incident_count=0,
    )
    db_session.add(ds)
    await db_session.flush()

    inc = Incident(
        id=str(uuid.uuid4()),
        dataset_id=ds.id,
        title="Test incident",
        status=IncidentStatus.NEW.value,
        severity=IncidentSeverity.MEDIUM.value,
        confidence=50,
    )
    db_session.add(inc)
    await db_session.commit()

    token = await _login(client, "analyst1")
    resp = await client.post(
        f"/incidents/{inc.id}/close",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_l2_can_close_incident(client: AsyncClient, db_session):
    """L2 should be able to close an incident."""
    import uuid
    from sqlalchemy import select
    from app.models.incident import Incident, IncidentStatus, IncidentSeverity
    from app.models.dataset import Dataset, DatasetStatus
    from app.models.user import User

    result = await db_session.execute(select(User).where(User.username == "analyst2"))
    analyst2 = result.scalar_one()

    ds = Dataset(
        id=str(uuid.uuid4()),
        name="test2",
        status=DatasetStatus.READY.value,
        uploaded_by=analyst2.id,
        event_count=0,
        incident_count=0,
    )
    db_session.add(ds)
    await db_session.flush()

    inc = Incident(
        id=str(uuid.uuid4()),
        dataset_id=ds.id,
        title="Test incident 2",
        status=IncidentStatus.NEW.value,
        severity=IncidentSeverity.HIGH.value,
        confidence=70,
    )
    db_session.add(inc)
    await db_session.commit()

    token = await _login(client, "analyst2")
    resp = await client.post(
        f"/incidents/{inc.id}/close",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "CLOSED"


async def test_admin_can_create_user(client: AsyncClient):
    token = await _login(client, "admin")
    resp = await client.post(
        "/users/",
        json={"username": "newuser", "password": "pass123", "role": "L1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["username"] == "newuser"
