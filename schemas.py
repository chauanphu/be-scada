# schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, time
from models.Audit import ActionEnum

class RoleCheck(BaseModel):
    role: int
    is_admin: bool

class RoleCreate(BaseModel):
    role_name: str
    permissions: list[int]

class PermissionRead(BaseModel):
    permission_id: int
    permission_name: str

    class Config:
        orm_mode = True

class RoleRead(BaseModel):
    role_id: int
    role_name: str
    
    class Config:
        orm_mode = True

class RoleReadFull(RoleRead):
    permissions: list[PermissionRead]

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: RoleRead

class UserReadShort(BaseModel):
    user_id: int
    username: str

    class Config:
        orm_mode = True

class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    permissions: Optional[list[int]] = None

class UserRead(BaseModel):
    user_id: int
    email: EmailStr
    username: str
    created: datetime
    updated: datetime
    role: RoleRead

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[RoleRead] = None

    class Config:
        orm_mode = True
        
class UnitBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode: True

class UnitCreate(BaseModel):
    name: str
    address: str

    class Config:
        orm_mode: True

class UnitUpdate(UnitBase):
    id: Optional[int] = None
    name: Optional[str] = None
    address: Optional[str] = None

class UnitRead(UnitBase):
    pass

class Unit(UnitBase):
    id: int
    cluster_id: int

    class Config:
        orm_mode: True

class ClusterBase(BaseModel):
    id: int
    name: str

class ClusterCreate(BaseModel):
    name: str
    units: list[UnitCreate]

class ClusterUpdate(ClusterBase):
    name: Optional[str] = None
    units: Optional[list[UnitUpdate]] = None

class ClusterRead(ClusterBase):
    units: list[UnitRead]
    class Config:
        orm_mode: True

class ClusterReadFull(ClusterBase):
    id: int
    name: str
    units: list[UnitRead]
    created: datetime
    updated: datetime
    class Config:
        orm_mode: True

class Cluster(ClusterBase):
    id: int
    account_id: int

    class Config:
        orm_mode: True

class Schedule(BaseModel):
    turn_on_time: time
    turn_off_time: time
    
class NodeControl(BaseModel):
    toggle: Optional[bool] = None
    schedule: Optional[Schedule] = None

class AuditLogResponse(BaseModel):
    timestamp: datetime
    email: EmailStr
    action: ActionEnum
    details: str

    class Config:
        orm_mode = True