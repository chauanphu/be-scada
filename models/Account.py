from sqlalchemy import Column, Integer, String, VARCHAR, Enum, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from database.__init__ import Base
from datetime import datetime

# Association table for Role and Permission
role_permission_table = Table(
    'role_permission',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('role.role_id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permission.permission_id'), primary_key=True)
)

class Permission(Base):
    """
    Represents a permission in the system.
    """
    __tablename__ = 'permission'
    
    permission_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    permission_name = Column(String, nullable=False, unique=True)

    roles = relationship('Role', secondary=role_permission_table, back_populates='permissions')
    
print("Permission model created successfully.")

class Role(Base):
    """
    Represents the role of a user in the system.
    """
    __tablename__ = 'role'
    
    role_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role_name = Column(String, nullable=False, unique=True)

    permissions = relationship('Permission', secondary=role_permission_table, back_populates='roles')

print("Role model created successfully.")

class Account(Base):
    """
    Represents account of a user in the system.
    """
    __tablename__ = 'account'
    
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    username = Column(VARCHAR(20), nullable=False, unique=True)
    password = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    role = Column(Integer, ForeignKey('role.role_id'), nullable=False, default=2)

    role_rel = relationship("Role", backref="account")

    def __repr__(self):
        return f"<Account {self.username}>"
    
print("Account model created successfully.")