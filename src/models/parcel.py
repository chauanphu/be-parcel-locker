from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from database.__init__ import Base


class Parcel(Base):
    """
    Represents a parcel in the system.
    """
    __tablename__ = 'parcel'
    
    parcel_id = Column(Integer, ForeignKey('order.order_id') ,primary_key=True)
    width = Column(Integer, nullable=False)
    length = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    parcel_size = Column(String, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    parcelType = Column(Integer, ForeignKey('parcel_type.parcel_type_id'))

print("Parcel model created successfully.")