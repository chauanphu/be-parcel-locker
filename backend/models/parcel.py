from sqlalchemy import Column, Integer, String, ForeignKey
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
    
    parcelType_id = Column(Integer, ForeignKey('parcel_type.parcel_type_id'))
    parcelTypes = relationship("ParcelType", back_populates="parcels")

print("Parcel model created successfully.")