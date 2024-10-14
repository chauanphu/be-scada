from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from database.__init__ import Base

class Status(Base):
    __tablename__ = "status"

    time = Column(TIMESTAMP(timezone=True), primary_key=True)

    power = Column(Float)
    current = Column(Float)
    voltage = Column(Float)
    toggle = Column(Boolean)
    power_factor = Column(Float)
    frequency = Column(Float)
    total_energy = Column(Float)
    
    unit_id = Column(Integer, ForeignKey('units.id'))
    unit = relationship('Unit', back_populates='statuses')

print("Status model created successfully.")