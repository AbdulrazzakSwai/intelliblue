from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from passlib.context import CryptContext
from ..database import get_db
from ..models.user import User
from ..schemas.auth import Token
from ..config import settings
from ..middleware.audit import record_audit

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(user_id: str, role: str, expires_delta: timedelta = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    data = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        await record_audit(db, "LOGIN_FAILURE", details=f"Failed login for {form_data.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")
    user.last_login = datetime.now(timezone.utc)
    await record_audit(db, "LOGIN_SUCCESS", user_id=str(user.id), details=f"Login: {user.username}")
    token = create_access_token(str(user.id), user.role.value)
    return Token(access_token=token, role=user.role.value, username=user.username)
