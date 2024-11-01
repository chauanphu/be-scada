from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, ForeignKey, Enum, String
from sqlalchemy.orm import relationship
from database.__init__ import Base
import enum

class TaskType(Base):
    __tablename__ = 'task_types'
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, unique=True, nullable=False)

# Populate the TaskType table with initial values
class TaskTypeEnum(enum.Enum):
    DISCONNECTION = "Mất kết nối"
    POWER_OFF = "Mất nguồn"
    FALSE_ACTIVE = "Hoạt động trái lệnh"

class TaskStatus(enum.Enum):
    PENDING = "Chưa xử lý"
    IN_PROGRESS = "Đang xử lý"
    COMPLETED = "Đã xử lý"

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(DateTime, default=datetime.utcnow)
    device_id = Column(Integer, ForeignKey('units.id'), nullable=False)
    type_id = Column(Integer, ForeignKey('task_types.id'), nullable=False)
    assignee_id = Column(Integer, ForeignKey('account.user_id'), nullable=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)

    device = relationship('Unit', back_populates='tasks')
    assignee = relationship('Account', back_populates='tasks')
    type = relationship('TaskType')

print("Task model created successfully.")