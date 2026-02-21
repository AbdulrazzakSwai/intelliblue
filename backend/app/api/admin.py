from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models.user import User
from ..models.audit_log import AuditLog
from ..schemas.audit import AuditLogOut
from ..middleware.rbac import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit-log", response_model=List[AuditLogOut])
async def get_audit_log(
    action_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    stmt = select(AuditLog)
    if action_type:
        stmt = stmt.where(AuditLog.action_type == action_type)
    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
