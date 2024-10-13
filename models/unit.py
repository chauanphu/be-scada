from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.__init__ import Base

class Cluster(Base):
    __tablename__ = 'clusters'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    account_id = Column(Integer, ForeignKey('account.user_id'))
    created = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    account = relationship('Account', back_populates='clusters')
    units = relationship("Unit", back_populates="cluster", cascade="all, delete-orphan")

class Unit(Base):
    __tablename__ = 'units'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    created = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    cluster = relationship('Cluster', back_populates='units')
    statuses = relationship('Status', back_populates='unit')

print("Unit, Cluster model created successfully.")