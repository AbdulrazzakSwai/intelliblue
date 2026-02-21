from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
import uuid
from ..database import get_db
from ..models.user import User, UserRole
from ..schemas.user import UserCreate, UserUpdate, UserOut
from ..middleware.rbac import require_admin, get_current_user
from ..middleware.audit import record_audit

router = APIRouter(prefix="/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/", response_model=List[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(User))
    return result.scalars().all()


@router.post("/", response_model=UserOut, status_code=201)
async def create_user(
    data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        id=str(uuid.uuid4()),
        username=data.username,
        password_hash=pwd_context.hash(data.password),
        role=UserRole(data.role),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()
    await record_audit(
        db, "USER_CREATE", user_id=str(current_user.id),
        target_type="User", target_id=str(user.id),
        after_json={"username": user.username, "role": user.role.value},
        ip_addr=request.client.host if request.client else None,
    )
    return user


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = await db.get(User, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    before = {"role": user.role.value, "is_active": user.is_active}
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = UserRole(data.role)
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.password is not None:
        user.password_hash = pwd_context.hash(data.password)
    await db.flush()
    await record_audit(
        db, "USER_UPDATE", user_id=str(current_user.id),
        target_type="User", target_id=str(user_id),
        before_json=before,
        after_json={"role": user.role.value, "is_active": user.is_active},
        ip_addr=request.client.host if request.client else None,
    )
    return user


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
