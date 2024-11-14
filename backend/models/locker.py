from sqlalchemy import Column, Float, ForeignKey, Integer, String, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from database.__init__ import Base
from sqlalchemy.orm import relationship
import enum

class SizeEnum(enum.Enum):
    S = 'S'
    M = 'M'
    L = 'L'

class Cell(Base):
    __tablename__ = 'cell'

    locker_id = Column(Integer, ForeignKey('locker.locker_id'), nullable=False)
    cell_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    size = Column(Enum(SizeEnum, name='size'), nullable=False)

class Locker(Base):
    __tablename__ = 'locker'

    locker_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    cells = relationship('Cell', backref='locker', lazy=True)