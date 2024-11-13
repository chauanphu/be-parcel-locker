from sqlalchemy import Column, Float, ForeignKey, Integer, String, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database.__init__ import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class Cell(Base):
    __tablename__ = 'cell'

    locker_id = Column(Integer, ForeignKey('locker.locker_id'), nullable=False)
    cell_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    size = Column(Enum('S', 'M', 'L', name='size'), nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)

    sending_orders = relationship('Order', 
                                foreign_keys='Order.sending_cell_id',
                                back_populates='sending_cell',
                                lazy=True)
    receiving_orders = relationship('Order',
                                  foreign_keys='Order.receiving_cell_id', 
                                  back_populates='receiving_cell',
                                  lazy=True)

class Locker(Base):
    __tablename__ = 'locker'

    locker_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    locker_status = Column(Enum('Active', 'Inactive', name='locker_status'), nullable=False, default='Active')
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)

    cells = relationship('Cell', backref='locker', lazy=True)