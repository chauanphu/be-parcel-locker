from sqlalchemy import Column, ForeignKey, Date, Integer, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.__init__ import Base
from datetime import datetime
import enum

class OrderStatus(enum.Enum):
    Completed = 'Completed'
    Canceled = 'Canceled'
    Ongoing = 'Ongoing'
    Delayed = 'Delayed'
    Expired = 'Expired'
    Packaging = 'Packaging'

class Order(Base):
    """
    Represents an order.
    """

    __tablename__ = 'order'

    order_id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('profile.user_id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('recipient.recipient_id'), nullable=False)
    sending_cell_id = Column(UUID, ForeignKey('cell.cell_id'), nullable=False)
    receiving_cell_id = Column(UUID, ForeignKey('cell.cell_id'), nullable=False)
    ordering_date = Column(Date, default=datetime.utcnow, nullable=False)
    sending_date = Column(Date)
    receiving_date = Column(Date)
    order_status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.Packaging, name='order_status')

    parcel = relationship('Parcel', backref='order', lazy=True, uselist=False)
    sender = relationship('Profile', backref='sender', lazy=True, uselist=False)
    recipient = relationship(
        "Recipient",
        foreign_keys=[recipient_id],
        back_populates="orders"
    )
    sending_cell = relationship('Cell', foreign_keys='Order.sending_cell_id', lazy=True, uselist=False)
    receiving_cell = relationship('Cell', foreign_keys='Order.receiving_cell_id', lazy=True, uselist=False)

print("Order model created successfully.")