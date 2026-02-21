"""
Folder-watcher placeholder for future streaming ingestion.

This module will watch a directory for new log files and feed them
through the ingestion pipeline using ingest_event().

Usage (future implementation):
    watcher = FolderWatcher(watch_dir="/var/log/siem", dataset_id="...", file_type="SIEM_JSON")
    await watcher.start()
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FolderWatcher:
    """
    Watches a folder for new log files and ingests them via ingest_event().

    Future implementation will:
    1. Monitor watch_dir for new files using inotify (Linux) or watchdog
    2. Detect file type from extension or explicit file_type parameter
    3. Parse new files using parse_content()
    4. Call ingest_event() for each NormalizedEvent
    5. Trigger correlation engine incrementally
    """

    def __init__(
        self,
        watch_dir: str,
        dataset_id: str,
        file_type: str = "SIEM_JSON",
        poll_interval: float = 5.0,
    ):
        self.watch_dir = Path(watch_dir)
        self.dataset_id = dataset_id
        self.file_type = file_type
        self.poll_interval = poll_interval
        self._running = False
        self._seen_files: set = set()

    async def start(self):
        """Start watching the folder. PLACEHOLDER - not yet implemented."""
        logger.info(f"FolderWatcher started for {self.watch_dir} (placeholder)")
        self._running = True
        # TODO: Implement file watching with asyncio + inotify or polling
        # while self._running:
        #     await self._check_new_files()
        #     await asyncio.sleep(self.poll_interval)

    async def stop(self):
        """Stop the folder watcher."""
        self._running = False
        logger.info("FolderWatcher stopped")

    async def _check_new_files(self):
        """Check for new files in the watch directory. PLACEHOLDER."""
        # TODO: For each new file:
        # 1. content = new_file.read_text()
        # 2. events = parse_content(content, self.file_type)
        # 3. async with AsyncSessionLocal() as db:
        #        for ne in events:
        #            await ingest_event(db, ne, self.dataset_id)
        #        await db.commit()
        pass
