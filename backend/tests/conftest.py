"""
Test fixtures: test DB (SQLite), test client, seeded users.
"""
import pytest
import pytest_asyncio
import uuid
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from passlib.context import CryptContext

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def seeded_users(db_session):
    users = {
        "admin": User(
            id=str(uuid.uuid4()),
            username="admin",
            password_hash=pwd_context.hash("admin123"),
            role=UserRole.ADMIN,
            full_name="Admin User",
            is_active=True,
        ),
        "analyst1": User(
            id=str(uuid.uuid4()),
            username="analyst1",
            password_hash=pwd_context.hash("analyst123"),
            role=UserRole.L1,
            full_name="L1 Analyst",
            is_active=True,
        ),
        "analyst2": User(
            id=str(uuid.uuid4()),
            username="analyst2",
            password_hash=pwd_context.hash("analyst123"),
            role=UserRole.L2,
            full_name="L2 Analyst",
            is_active=True,
        ),
    }
    for user in users.values():
        db_session.add(user)
    await db_session.commit()
    return users


@pytest_asyncio.fixture(scope="function")
async def client(db_engine, seeded_users) -> AsyncGenerator[AsyncClient, None]:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
