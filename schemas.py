# schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, time

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: Optional[int] = 2

class UserReadShort(BaseModel):
    user_id: int
    email: EmailStr

    class Config:
        orm_mode = True

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

class UnitBase(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float

class UnitCreate(UnitBase):
    pass

class UnitUpdate(UnitBase):
    pass

class UnitRead(UnitBase):
    name: str
    address: str
    latitude: float
    longitude: float

    class Config:
        orm_mode: True

class Unit(UnitBase):
    id: int
    cluster_id: int

    class Config:
        orm_mode: True

class ClusterBase(BaseModel):
    name: str

class ClusterCreate(ClusterBase):
    account_id: int
    units: list[UnitCreate]

class ClusterUpdate(ClusterBase):
    pass

class ClusterRead(ClusterBase):
    id: int
    name: str
    units: list[UnitRead]
    class Config:
        orm_mode: True

class ClusterReadFull(ClusterBase):
    id: int
    name: str
    units: list[UnitRead]
    account: UserReadShort
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