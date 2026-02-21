from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.audit_log import AuditLog


async def record_audit(
    db: AsyncSession,
    action_type: str,
    user_id: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    before_json=None,
    after_json=None,
    details: Optional[str] = None,
    ip_addr: Optional[str] = None,
):
    entry = AuditLog(
        user_id=user_id,  # Pass as string directly
        action_type=action_type,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        before_json=before_json,
        after_json=after_json,
        details=details,
        ip_addr=ip_addr,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.flush()
