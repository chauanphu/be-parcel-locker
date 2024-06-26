from sqlalchemy import Column, ForeignKey, String, VARCHAR, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.__init__ import Base

class Order(Base):
    """
    Represents an order.
    """

    __tablename__ = 'order'

    order_id = Column(Integer,primary_key=True, index=True) 
    sender_id = Column(Integer, nullable=False)
    recipient_id = Column(Integer, nullable=False)
    sending_cell_id = Column(UUID, ForeignKey('cell.cell_id'), nullable=False)
    receiving_cell_id = Column(UUID, ForeignKey('cell.cell_id'), nullable=False)
    ordering_date = Column(Date) 
    sending_date = Column(Date)
    receiving_date = Column(Date)
    
    parcel = relationship( 'Parcel', backref= 'order',lazy=True, uselist=False)
    
print("Order model created successfully.")