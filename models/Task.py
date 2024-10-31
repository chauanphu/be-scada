from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database.__init__ import Base
import enum

class TaskType(enum.Enum):
    DISCONNECTION = "disconnection"
    POWERLOST = "powerlost"
    REPAIR = "repair"

class TaskStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "PROGRESS"
    COMPLETED = "COMPLETED"

class Task(Base):
    __tablename__ = 'tasks'
    time = Column(DateTime, primary_key=True, default=datetime.utcnow)
    device_id = Column(Integer, ForeignKey('units.id'), nullable=False)
    type = Column(Enum(TaskType), nullable=False)
    assignee_id = Column(Integer, ForeignKey('account.user_id'), nullable=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)

    device = relationship('Unit', back_populates='tasks')
    assignee = relationship('Account', back_populates='tasks')

print("Task model created successfully.")