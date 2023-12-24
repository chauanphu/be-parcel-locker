from sqlalchemy import Boolean, Column, Float, Integer, String
from database.__init__ import Base

class LockerStatus(Base):
    __tablename__ = 'locker_status'

    locker_id = Column(Integer, primary_key=True)
    cell = Column(Integer, nullable=False)
    occupied = Column(Boolean, nullable=False, default=False)