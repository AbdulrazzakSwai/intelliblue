#!/usr/bin/env python3
"""
Seed demo data by uploading sample files and processing them.

Usage: python scripts/seed_demo_data.py
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.config import settings
from app.models.user import User
from app.models.dataset import Dataset, DatasetStatus
from app.models.raw_file import RawFile, FileType
from app.ingestion.file_handler import store_file
from app.ingestion.pipeline import parse_content, ingest_batch
from app.correlation.engine import correlate_dataset
import uuid

SAMPLE_FILES = [
    ("siem_export.ndjson", "SIEM_JSON"),
    ("access.log", "WEB_LOG"),
    ("suricata_alerts.json", "SURICATA"),
    ("snort_alerts.json", "SNORT"),
]

SAMPLE_DATA_DIR = Path(__file__).parent.parent / "sample_data"


async def seed():
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Get admin user
        result = await session.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()
        if not admin:
            print("Admin user not found. Run seed_users.py first.")
            return

        # Create dataset
        dataset = Dataset(
            id=str(uuid.uuid4()),
            name="Demo Dataset - January 2024",
            description="Sample data showing brute force, web scanning, and IDS alerts",
            uploaded_by=admin.id,
            status=DatasetStatus.PARSING.value,
        )
        session.add(dataset)
        await session.flush()
        print(f"Created dataset: {dataset.name}")

        total_events = 0
        for filename, file_type in SAMPLE_FILES:
            path = SAMPLE_DATA_DIR / filename
            if not path.exists():
                print(f"  Sample file not found: {path}")
                continue

            content_bytes = path.read_bytes()
            stored_path, sha256 = store_file(content_bytes, filename, str(dataset.id))

            raw_file = RawFile(
                id=str(uuid.uuid4()),
                dataset_id=dataset.id,
                filename=filename,
                file_type=FileType(file_type),
                sha256=sha256,
                stored_path=stored_path,
                size_bytes=len(content_bytes),
            )
            session.add(raw_file)
            await session.flush()

            normalized = parse_content(content_bytes.decode("utf-8", errors="replace"), file_type)
            persisted = await ingest_batch(session, normalized, dataset.id, str(raw_file.id))
            total_events += len(persisted)
            print(f"  Ingested {len(persisted)} events from {filename}")

        dataset.event_count = total_events
        dataset.status = DatasetStatus.CORRELATING.value
        await session.commit()

        # Run correlation
        print("Running correlation engine...")
        async with session_factory() as corr_session:
            incidents = await correlate_dataset(corr_session, str(dataset.id))
            ds = await corr_session.get(Dataset, str(dataset.id))
            ds.status = DatasetStatus.READY.value
            await corr_session.commit()
            print(f"Created {len(incidents)} incidents")

    await engine.dispose()
    print(f"\nDemo data seeded! {total_events} events, check the dashboard.")


if __name__ == "__main__":
    asyncio.run(seed())
