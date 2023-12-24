from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from database.__init__ import Base
from sqlalchemy.orm import relationship

class Locker(Base):
    __tablename__ = 'locker'

    locker_id = Column(Integer, ForeignKey('locker_status.locker_id'), primary_key=True)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    cells = relationship('LockerStatus', backref='locker', lazy=True)