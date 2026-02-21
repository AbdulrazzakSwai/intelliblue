import pytest
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.models.dataset import Dataset, DatasetStatus
from app.models.event import Event
from app.models.incident import Incident
from app.correlation.rules.brute_force import run as brute_force_run

pytestmark = pytest.mark.asyncio

CONFIG = {"brute_force_window_minutes": 10, "brute_force_threshold": 5}


async def _create_dataset(db_session, username="admin"):
    from sqlalchemy import select
    from app.models.user import User
    result = await db_session.execute(select(User).where(User.username == username))
    user = result.scalar_one()
    ds = Dataset(
        id=str(uuid.uuid4()),
        name="corr_test",
        status=DatasetStatus.READY.value,
        uploaded_by=user.id,
        event_count=0,
        incident_count=0,
    )
    db_session.add(ds)
    await db_session.flush()
    return ds


async def _create_login_failures(db_session, dataset_id, src_ip, count, start_time=None):
    if start_time is None:
        start_time = datetime.now(timezone.utc)
    events = []
    for i in range(count):
        ev = Event(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            source_type="SIEM_JSON",
            event_type="login_failure",
            src_ip=src_ip,
            username="alice",
            event_time=start_time + timedelta(minutes=i),
        )
        db_session.add(ev)
        events.append(ev)
    await db_session.flush()
    return events


async def test_brute_force_fires_above_threshold(db_session, seeded_users):
    ds = await _create_dataset(db_session)
    await _create_login_failures(db_session, ds.id, "192.168.1.100", 6)
    await db_session.commit()

    incidents = await brute_force_run(db_session, str(ds.id), CONFIG)
    assert len(incidents) == 1
    assert incidents[0].incident_type == "brute_force"
    assert incidents[0].confidence > 0
    assert "192.168.1.100" in incidents[0].title


async def test_brute_force_does_not_fire_below_threshold(db_session, seeded_users):
    ds = await _create_dataset(db_session)
    await _create_login_failures(db_session, ds.id, "10.0.0.1", 3)
    await db_session.commit()

    incidents = await brute_force_run(db_session, str(ds.id), CONFIG)
    assert len(incidents) == 0


async def test_brute_force_exactly_at_threshold(db_session, seeded_users):
    ds = await _create_dataset(db_session)
    await _create_login_failures(db_session, ds.id, "10.0.0.5", 5)
    await db_session.commit()

    incidents = await brute_force_run(db_session, str(ds.id), CONFIG)
    assert len(incidents) == 1


async def test_brute_force_not_duplicated(db_session, seeded_users):
    """Running correlation twice should not create duplicate incidents."""
    ds = await _create_dataset(db_session)
    await _create_login_failures(db_session, ds.id, "172.16.0.1", 8)
    await db_session.commit()

    incidents1 = await brute_force_run(db_session, str(ds.id), CONFIG)
    await db_session.commit()
    incidents2 = await brute_force_run(db_session, str(ds.id), CONFIG)
    await db_session.commit()

    assert len(incidents1) == 1
    assert len(incidents2) == 0  # No duplicates
