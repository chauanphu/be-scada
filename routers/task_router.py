from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from database import session
from database.session import get_db
from models.Account import Account, Permission, Role
from models.Task import Task

router = APIRouter(
    prefix='/tasks',
    tags=['tasks']
)

class TaskRead(BaseModel):
    time: datetime
    device: str
    type: str
    status: str
    assigned_to: str

    class Config:
        orm_mode = True

class Assignee(BaseModel):
    id: int
    email: str

    class Config:
        orm_mode = True

@router.get("/")
async def get_tasks(
    page: int = 1,
    page_size: int = 10,
    typeFilter: str = None,
    statusFilter: str = None,
    db: session = Depends(get_db)
):
    query = db.query(Task)

    if typeFilter:
        query = query.filter(Task.type == typeFilter)
    if statusFilter:
        query = query.filter(Task.status == statusFilter)

    total = query.count()
    tasks: list[Task] = query.order_by(Task.time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    tasks = [
        TaskRead(
            time=task.time, 
            device=task.device.name, 
            type=task.type, 
            status=task.status, 
            assigned_to=task.assignee if task.assignee else "Chưa được giao"
        )
        for task in tasks
    ]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [TaskRead.model_validate(task) for task in tasks]
    }

# Get assignees
@router.get("/assignees")
async def get_assignees(db: session = Depends(get_db)):
    # Get all role ids that have the permission CONTROL_DEVICE and MONITOR_SYSTEM
    role_ids = db.query(Role).filter(
        Role.permissions.any(Permission.permission_name.in_(['GIÁM SÁT HỆ THỐNG', 'ĐIỀU KHIỂN THIẾT BỊ']))
    ).all()
    # Get all accounts that have the role_id in the list
    accounts: list[Account] = db.query(Account).filter(Account.role.in_([role.role_id for role in role_ids])).all()
    
    return [
        Assignee(id=account.user_id, email=account.email) for account in accounts
    ]
