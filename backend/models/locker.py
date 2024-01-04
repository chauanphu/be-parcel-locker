from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, PrimaryKeyConstraint, String
from database.__init__ import Base
from sqlalchemy.orm import relationship

class LockerStatus(Base):
    __tablename__ = 'locker_status'

    locker_id = Column(Integer, ForeignKey('locker.locker_id'))
    cell_id = Column(Integer, nullable=False)
    occupied = Column(Boolean, nullable=False, default=False)
    PrimaryKeyConstraint(locker_id, cell_id)
    
class Locker(Base):
    __tablename__ = 'locker'

    locker_id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    cells = relationship('LockerStatus', backref='locker', lazy=True)