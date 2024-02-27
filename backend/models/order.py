from datetime import date
from sqlalchemy import Column, String, VARCHAR, Date
from database.__init__ import Base

class Order(Base):
    """
    Represents an order.
    """

    __tablename__ = 'order here!'

    package = Column(String,primary_key=True, index=True) 
    sender = Column(VARCHAR(20), nullable=False)
    recipient = Column(VARCHAR(20), nullable=False)
    sending_locker = Column(String, nullable=False)
    receiving_locker= Column(String, nullable=False)
    sending_date = Column(Date)
    receiving_date = Column(Date)

print("Order model created successfully.")