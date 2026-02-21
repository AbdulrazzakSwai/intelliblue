import hashlib
import shutil
from pathlib import Path
from ..config import settings


def store_file(content: bytes, filename: str, dataset_id: str) -> tuple[str, str]:
    """Store raw file content and return (stored_path, sha256)."""
    sha256 = hashlib.sha256(content).hexdigest()
    upload_dir = Path(settings.upload_dir) / dataset_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / f"{sha256}_{filename}"
    dest.write_bytes(content)
    return str(dest), sha256
