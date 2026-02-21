"""
Main correlation orchestrator.
Runs all rules against a dataset and returns created incidents.
"""
import json
from pathlib import Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.incident import Incident
from ..models.dataset import Dataset
from ..config import settings
from .rules import brute_force, web_scanning, ids_confirmed


def _load_config() -> dict:
    path = Path(settings.correlation_config_path)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {
        "brute_force_window_minutes": 10,
        "brute_force_threshold": 5,
        "web_scan_window_minutes": 5,
        "web_scan_url_threshold": 20,
        "web_scan_error_threshold": 10,
        "ids_correlation_window_minutes": 10,
    }


async def correlate_dataset(db: AsyncSession, dataset_id: str) -> List[Incident]:
    """Run all correlation rules against a dataset."""
    config = _load_config()
    all_incidents = []

    bf_incidents = await brute_force.run(db, dataset_id, config)
    all_incidents.extend(bf_incidents)

    ws_incidents = await web_scanning.run(db, dataset_id, config)
    all_incidents.extend(ws_incidents)

    ids_incidents = await ids_confirmed.run(db, dataset_id, config)
    all_incidents.extend(ids_incidents)

    # Update dataset incident count
    result = await db.execute(
        select(func.count(Incident.id)).where(Incident.dataset_id == dataset_id)
    )
    count = result.scalar() or 0
    dataset = await db.get(Dataset, dataset_id)
    if dataset:
        dataset.incident_count = count

    await db.flush()
    return all_incidents
