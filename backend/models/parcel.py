from sqlalchemy import Column, Integer, String, Sequence, VARCHAR , ForeignKey, Float,PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from database.__init__ import Base


class Parcel(Base):
    """
    Represents a parcel in the system.
    """
    __tablename__ = 'parcel'
    
    order_id = Column(Integer, ForeignKey('order_table.order_id'))
    parcel_id = Column(Integer, Sequence('parcel_id_seq'))
    width = Column(Integer, nullable=False)
    length = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    parcel_size = Column(String, nullable=False) 
    PrimaryKeyConstraint(order_id, parcel_id)
    order = relationship('Order', back_populates='parcels')

print("Parcel model created successfully.")