#!/usr/bin/env python3
"""
Seed default users for IntelliBlue SOC.

Usage: python scripts/seed_users.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from passlib.context import CryptContext
from app.config import settings
from app.database import Base
from app.models.user import User, UserRole
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

USERS = [
    {"username": "admin", "password": "admin123", "role": "ADMIN", "full_name": "System Administrator"},
    {"username": "analyst1", "password": "analyst123", "role": "L1", "full_name": "L1 Analyst"},
    {"username": "analyst2", "password": "analyst123", "role": "L2", "full_name": "L2 Analyst"},
]


async def seed():
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        for u in USERS:
            from sqlalchemy import select
            existing = await session.execute(select(User).where(User.username == u["username"]))
            if existing.scalar_one_or_none():
                print(f"  User '{u['username']}' already exists, skipping")
                continue
            user = User(
                id=str(uuid.uuid4()),
                username=u["username"],
                password_hash=pwd_context.hash(u["password"]),
                role=UserRole(u["role"]),
                full_name=u["full_name"],
                is_active=True,
            )
            session.add(user)
            print(f"  Created user: {u['username']} ({u['role']})")
        await session.commit()
    await engine.dispose()
    print("Users seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
