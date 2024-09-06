from sqlalchemy import Column, Integer, String, Sequence, VARCHAR , ForeignKey, Float,PrimaryKeyConstraint,DateTime
from datetime import datetime

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


print("Parcel model created successfully.")