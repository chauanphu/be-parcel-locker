from sqlalchemy import Column, String, Date, VARCHAR, ForeignKey, PrimaryKeyConstraint, Integer, Sequence
from sqlalchemy.orm import relationship
from database.__init__ import Base

class Order(Base):
    """
    Represents an order.
    """

    __tablename__ = 'order_table'

    order_id = Column(Integer, Sequence('order_id_seq'))
    sender_id = Column(VARCHAR(20), nullable=False)
    recipient_id = Column(VARCHAR(20), nullable=False)
    sending_locker_id = Column(String, nullable=False)
    receiving_locker_id = Column(String, nullable=False)
    ordering_date = Column(Date) 
    sending_date = Column(Date)
    receiving_date = Column(Date)
    PrimaryKeyConstraint(order_id)
    parcels = relationship("Parcel", back_populates="order", lazy=True)

print("Order model created successfully.")
