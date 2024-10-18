import datetime
import enum
from sqlalchemy import Column, DateTime, String, Enum
from sqlalchemy.orm import relationship
from database.__init__ import Base

class ActionEnum(enum.Enum):
    CREATE = "TẠO"
    UPDATE = "CẬP NHẬT"
    DELETE = "XÓA"
    LOGIN = "ĐĂNG NHẬP"
    LOGOUT = "ĐĂNG XUẤT"
    READ = "ĐỌC"

class Audit(Base):
    __tablename__ = 'audit'
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, primary_key=True)
    email = Column(String(255), nullable=False)
    action = Column(Enum(ActionEnum), nullable=False, index=True)
    details = Column(String(255), nullable=False)

print("Audit model created successfully.")