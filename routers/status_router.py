from datetime import datetime, timedelta
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from database import session
from database.session import get_db
from models.Account import Account
from models.Status import Status
from routers.dependencies import admin_required
from utils import get_tz_datetime
from typing import Optional

router = APIRouter(
    prefix='/status',
    tags=['status']
)

# Enum for the view parameter
class ViewEnum(str, Enum):
    hourly = "hourly"
    daily = "daily"
    monthly = "monthly"

class EnergyRead(BaseModel):
    time: datetime
    total_energy: float

    class Config:
        orm_mode = True

def get_grouped_data(view: ViewEnum, db, device_id=None, start_date=None, end_date=None):
    current_time = get_tz_datetime()
    if start_date and end_date:
        start = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end_date.replace(hour=23, minute=59, second=59, microsecond=0)
    else:
        if view == ViewEnum.hourly:
            start = current_time - timedelta(hours=1)
        elif view == ViewEnum.daily:
            start = current_time - timedelta(days=1)
        elif view == ViewEnum.monthly:
            start = current_time - timedelta(days=30)
        else:
            raise ValueError("Invalid view type")
        end = current_time

    if view == ViewEnum.hourly:
        time_format = func.date_trunc('hour', Status.time)
    elif view == ViewEnum.daily:
        time_format = func.date_trunc('day', Status.time)
    elif view == ViewEnum.monthly:
        time_format = func.date_trunc('month', Status.time)
    else:
        raise ValueError("Invalid view type")

    result = db.query(
        time_format.label("time"),
        func.sum(Status.total_energy).label("total_energy")
    ).filter(
        Status.time >= start,
        Status.time <= end,
        Status.unit_id == device_id if device_id else True
    ).group_by(
        time_format
    ).order_by(
        time_format.asc()  # Ensure ordering by time in ascending order
    ).all()

    return result

# Return energy consumption, query: view=hourly|daily|monthly, start_date, end_date
@router.get("/energy", response_model=list[EnergyRead])
def get_energy(view: ViewEnum, db: session = Depends(get_db), current_user: Account = Depends(admin_required), start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    try:
        result = get_grouped_data(view, db, start_date=start_date, end_date=end_date)
        return result
    except ValueError as e:
        return {"error": str(e)}
    
@router.get("/energy/{device_id}", response_model=list[EnergyRead])
def get_energy_by_device_id(device_id: int, view: ViewEnum, db: session = Depends(get_db), current_user: Account = Depends(admin_required), start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    device = db.query(Status).filter(Status.unit_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    result = get_grouped_data(view, db, device_id, start_date, end_date)
    return result
