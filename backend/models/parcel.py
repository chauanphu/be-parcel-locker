from sqlalchemy import Column, Integer, String, Sequence, VARCHAR , ForeignKey, Float,PrimaryKeyConstraint

from database.__init__ import Base
from models.order import Order


class Parcel(Base):
    """
    Represents a parcel in the system.
    """
    __tablename__ = 'parcel'
    
    parcel_id = Column(String, ForeignKey('order.parcel_id') ,primary_key=True)
    width = Column(Float, nullable=False)
    length = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    parcel_size = Column(String, nullable=False) 


print("Parcel model created successfully.")