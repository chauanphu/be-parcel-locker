from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database.__init__ import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class Cell(Base):
    __tablename__ = 'cell'

    locker_id = Column(Integer, ForeignKey('locker.locker_id'), nullable=False,)
    cell_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    size = Column(Enum('S', 'M', 'L', name='size'), nullable=False)
    occupied = Column(Boolean, nullable=False, default=False)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)

print ("Cell model created successfully.")
class Locker(Base):
    __tablename__ = 'locker'

    locker_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    locker_status = Column(Enum('Active', 'Inactive', name='locker_status'), nullable=False,default='Active')
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)


    cells = relationship('Cell', backref='locker', lazy=True)

print ("Locker model created successfully.")