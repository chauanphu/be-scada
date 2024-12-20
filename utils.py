# utils.py

from datetime import datetime
from passlib.context import CryptContext
import pytz
from models.Account import Account
from models.Audit import Audit
from models.Task import TaskType, TaskTypeEnum

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def save_audit_log(db, email: str, action: str, details: str):
    user = db.query(Account).filter(Account.email == email).first()
    if user.role_rel.role_name == "SUPERADMIN":
        return None
    audit = Audit(email=email, action=action, details=details)
    db.add(audit)
    db.commit()
    return audit

def get_tz_datetime(timestamp: int | None = None) -> datetime:
    if not timestamp:
        # Get current time
        return datetime.now(pytz.UTC)
    else:   
        utc_dt = datetime.fromtimestamp(timestamp, pytz.UTC)
        time = utc_dt.replace(tzinfo=pytz.FixedOffset(420))
        return time

def add_task(device_id: int, type: TaskTypeEnum):
    from models.Task import Task, TaskStatus
    from database.__init__ import SessionLocal

    session = SessionLocal()
    try:
        # Check if there is an unresolved task for the device with the same type
        task_type = session.query(TaskType).filter(TaskType.value == type.value).first()
        existing_task = session.query(Task).filter(
            Task.device_id == device_id, 
            Task.type == task_type,
            Task.status != TaskStatus.COMPLETED).first()
        
        if existing_task:
            session.close()
            return
        task = Task(
            device_id=device_id,
            type=task_type
        )
        session.add(task)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error adding task: {e}")
    finally:
        session.close()