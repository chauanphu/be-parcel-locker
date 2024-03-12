from sqlalchemy import Column, String, VARCHAR, Date
from sqlalchemy.orm import relationship
from database.__init__ import Base

class Order(Base):
    """
    Represents an order.
    """

    __tablename__ = 'order'

    parcel_id = Column(String,primary_key=True, index=True) 
    sender_id = Column(VARCHAR(20), nullable=False)
    recipient_id = Column(VARCHAR(20), nullable=False)
    sending_locker_id = Column(String, nullable=False)
    receiving_locker_id = Column(String, nullable=False)
    ordering_date = Column(Date) 
    sending_date = Column(Date)
    receiving_date = Column(Date)
    
    order = relationship( 'Parcel', backref= 'order',lazy=True)

print("Order model created successfully.")