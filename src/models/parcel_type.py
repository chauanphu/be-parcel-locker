from sqlalchemy import Column, Integer, String

from database.__init__ import Base


class ParcelType(Base):
    """
    Represents a type of parcel in the system.
    """
    __tablename__ = 'parcel_type'
    
    parcel_type_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) 


print("ParcelType model created successfully.")