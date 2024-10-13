import datetime
import enum
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Enum
from sqlalchemy.orm import relationship
from database.__init__ import Base

class ActionEnum(enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOG IN"
    LOGOUT = "LOG OUT"
    READ = "READ"

class Audit(Base):
    __tablename__ = 'audit'
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, primary_key=True)
    user_id = Column(Integer, ForeignKey('account.user_id'))
    action = Column(Enum(ActionEnum), nullable=False, index=True)
    details = Column(String(255), nullable=False)

    user = relationship('Account', backref='audits')

print("Audit model created successfully.")