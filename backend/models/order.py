from datetime import date
from sqlalchemy import Column, String, VARCHAR
from database.__init__ import Base

class Order(Base):
    """
    Represents an order.
    """

    __tablename__ = 'order here!'

    package: Column(String) 
    sender: Column(VARCHAR(20))
    recipient: Column(VARCHAR(20))
    sending_locker: Column(String)
    receiving_locker: Column(String)
    sending_date: Column(date)
    receiving_date: Column(date)