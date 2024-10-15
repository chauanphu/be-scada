from datetime import datetime, timedelta
from enum import Enum
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from database import session
from database.session import get_db
from models.Account import Account
from models.Status import Status
from routers.dependencies import admin_required

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

def get_grouped_data(view: ViewEnum, db):
    if view == ViewEnum.hourly:
        start = datetime.now() - timedelta(hours=1)
        time_format = func.date_trunc('minute', Status.time)
    elif view == ViewEnum.daily:
        start = datetime.now() - timedelta(days=1)
        time_format = func.date_trunc('hour', Status.time)
    elif view == ViewEnum.monthly:
        start = datetime.now() - timedelta(days=30)
        time_format = func.date_trunc('day', Status.time)
    else:
        raise ValueError("Invalid view type")

    result = db.query(
        time_format.label("time"),
        func.sum(Status.total_energy).label("total_energy")
    ).filter(
        Status.time >= start
    ).group_by(
        time_format
    ).all()

    return result

# Return enerygy consumption, query: view=hourly|daily|monthly
@router.get("/enery", response_model=list[EnergyRead])
def get_energy(view: ViewEnum, db: session = Depends(get_db), current_user: Account = Depends(admin_required)):
    try:
        result = get_grouped_data(view, db)
        return result
    except ValueError as e:
        return {"error": str(e)}
