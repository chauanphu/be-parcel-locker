from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.__init__ import Base


class ParcelType(Base):
    """
    Represents a type of parcel in the system.
    """
    __tablename__ = 'parcel_type'
    
    parcel_type_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) 
    parcels = relationship("Parcel", back_populates="parcelTypes")

print("ParcelType model created successfully.")