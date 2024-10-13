# schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: Optional[int] = 2

class UserRead(BaseModel):
    user_id: int
    email: EmailStr
    username: str
    status: str
    created: datetime
    updated: datetime
    role: int

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    username: Optional[str]
    password: Optional[str]
    status: Optional[str]
    role: Optional[int]
