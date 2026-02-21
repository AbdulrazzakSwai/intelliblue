import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..database import get_db, AsyncSessionLocal
from ..models.user import User
from ..models.dataset import Dataset, DatasetStatus
from ..models.raw_file import RawFile, FileType
from ..models.event import Event
from ..schemas.dataset import DatasetOut, DatasetList
from ..middleware.rbac import require_admin, require_l1
from ..middleware.audit import record_audit
from ..ingestion.file_handler import store_file
from ..ingestion.pipeline import parse_content, ingest_batch
from ..correlation.engine import correlate_dataset

router = APIRouter(prefix="/datasets", tags=["datasets"])


async def _process_dataset(dataset_id: str, files_data: list):
    """Background task: parse files, ingest events, correlate."""
    async with AsyncSessionLocal() as db:
        try:
            dataset = await db.get(Dataset, str(dataset_id))
            if not dataset:
                return

            dataset.status = DatasetStatus.PARSING.value
            await db.commit()

            total_events = 0
            parse_errors = []

            for file_type, filename, content in files_data:
                raw_file = await db.execute(
                    select(RawFile).where(
                        RawFile.dataset_id == dataset_id,
                        RawFile.filename == filename,
                    )
                )
                raw_file_obj = raw_file.scalar_one_or_none()

                try:
                    normalized = parse_content(content, file_type)
                    persisted = await ingest_batch(
                        db, normalized, dataset_id,
                        raw_file_id=str(raw_file_obj.id) if raw_file_obj else None
                    )
                    total_events += len(persisted)
                except Exception as e:
                    parse_errors.append({"file": filename, "error": str(e)})

            dataset = await db.get(Dataset, str(dataset_id))
            dataset.event_count = total_events
            dataset.parse_errors = parse_errors
            dataset.status = DatasetStatus.CORRELATING.value
            await db.commit()

            # Correlation
            await correlate_dataset(db, dataset_id)

            dataset = await db.get(Dataset, str(dataset_id))
            dataset.status = DatasetStatus.READY.value
            await db.commit()

        except Exception as e:
            async with AsyncSessionLocal() as db2:
                dataset = await db2.get(Dataset, dataset_id)
                if dataset:
                    dataset.status = DatasetStatus.ERROR.value
                    dataset.parse_errors = [{"error": str(e)}]
                    await db2.commit()


@router.get("/", response_model=List[DatasetList])
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    result = await db.execute(select(Dataset).order_by(Dataset.uploaded_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=DatasetOut, status_code=201)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    files: List[UploadFile] = File(...),
    file_types: List[str] = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    dataset = Dataset(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        uploaded_by=current_user.id,
        status=DatasetStatus.UPLOADING.value,
    )
    db.add(dataset)
    await db.flush()

    files_data = []
    for upload_file, file_type in zip(files, file_types):
        content_bytes = await upload_file.read()
        stored_path, sha256 = store_file(content_bytes, upload_file.filename, str(dataset.id))
        raw_file = RawFile(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            filename=upload_file.filename,
            file_type=FileType(file_type),
            sha256=sha256,
            stored_path=stored_path,
            size_bytes=len(content_bytes),
        )
        db.add(raw_file)
        files_data.append((file_type, upload_file.filename, content_bytes.decode("utf-8", errors="replace")))

    await db.flush()
    await record_audit(
        db, "DATASET_UPLOAD", user_id=str(current_user.id),
        target_type="Dataset", target_id=str(dataset.id),
        after_json={"name": name},
        ip_addr=request.client.host if request.client else None,
    )
    await db.commit()

    background_tasks.add_task(_process_dataset, str(dataset.id), files_data)
    dataset_out = await db.get(Dataset, dataset.id)
    return dataset_out


@router.get("/{dataset_id}", response_model=DatasetOut)
async def get_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_l1),
):
    dataset = await db.get(Dataset, str(dataset_id))
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    dataset = await db.get(Dataset, str(dataset_id))
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    await record_audit(
        db, "DATASET_DELETE", user_id=str(current_user.id),
        target_type="Dataset", target_id=str(dataset_id),
        before_json={"name": dataset.name},
        ip_addr=request.client.host if request.client else None,
    )
    await db.delete(dataset)
