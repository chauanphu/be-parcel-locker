from sqlalchemy import Column, String, VARCHAR, Date
from database.__init__ import Base

class Order(Base):
    """
    Represents an order.
    """

    __tablename__ = 'order'

    package_id = Column(String,primary_key=True, index=True) 
    sender_id = Column(VARCHAR(20), nullable=False)
    recipient_id = Column(VARCHAR(20), nullable=False)
    sending_locker_id = Column(String, nullable=False)
    receiving_locker_id = Column(String, nullable=False)
    ordering_date = Column(Date) 
    sending_date = Column(Date)
    receiving_date = Column(Date)

print("Order model created successfully.")

class Send(Base):
    """
    Represents a send.
    """
    __tablename__ = 'send'

    package_id = Column(String,primary_key=True, index=True) 
    sender_id = Column(VARCHAR(20), nullable=False)
    recipient_id = Column(VARCHAR(20), nullable=False)
    name_recipient = Column(String, nullable=False)
    phone_recipient =  Column(String, nullable=False)
    address_recipient = Column(String, nullable=False)
    sending_locker_id = Column(String, nullable=False)
    receiving_locker_id = Column(String, nullable=False)
    ordering_date = Column(Date) 
    sending_date = Column(Date)
    receiving_date = Column(Date)

print("Send model created successfully.")