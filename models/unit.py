from datetime import datetime, time
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, ForeignKey, Time
from sqlalchemy.orm import relationship
from database.__init__ import Base

class Cluster(Base):
    __tablename__ = 'clusters'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    created = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    units = relationship("Unit", back_populates="cluster", cascade="all, delete-orphan")

class Unit(Base):
    __tablename__ = 'units'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    mac = Column(String, nullable=False, unique=True)
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    toggle = Column(Boolean, default=False)
    # On time and Off time
    on_time = Column(Time, nullable=False, default=time(18, 0, 0))  # 6:00 PM
    off_time = Column(Time, nullable=False, default=time(5, 0, 0))  # 5:00 AM

    created = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    cluster = relationship('Cluster', back_populates='units')
    statuses = relationship('Status', back_populates='unit')
    tasks = relationship('Task', back_populates='device')

print("Unit, Cluster model created successfully.")