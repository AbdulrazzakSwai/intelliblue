from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
import uuid


class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    role: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
