from sqlalchemy import Column, ForeignKey, Date, Integer, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.__init__ import Base
from datetime import datetime
import enum
from models.account import Account

class OrderStatus(enum.Enum):
    Completed = 'Completed'
    Canceled = 'Canceled'
    Ongoing = 'Ongoing'
    Delayed = 'Delayed'
    Expired = 'Expired'
    Packaging = 'Packaging'

order_status_enum = SqlEnum(OrderStatus, name='order_status')

class Order(Base):
    """
    Represents an order.
    """

    __tablename__ = 'order'

    order_id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('account.user_id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('account.user_id'), nullable=False)
    sending_cell_id = Column(UUID, ForeignKey('cell.cell_id'), nullable=False)
    receiving_cell_id = Column(UUID, ForeignKey('cell.cell_id'), nullable=False)
    ordering_date = Column(Date, default=datetime.utcnow, nullable=False)
    sending_date = Column(Date)
    receiving_date = Column(Date)
    order_status = Column(order_status_enum, nullable=False, default=OrderStatus.Packaging, name='order_status')

    parcel = relationship('Parcel', backref='order', lazy=True, uselist=False)
    sender = relationship(
    'Account',
    backref='sent_orders',
    lazy=True,
    uselist=False,
    foreign_keys=[sender_id]
    )
    recipient = relationship(
        'Account',
        backref='received_orders',
        lazy=True,
        uselist=False,
        foreign_keys=[recipient_id]
    )
    sending_cell = relationship('Cell', foreign_keys='Order.sending_cell_id', lazy=True, uselist=False)
    receiving_cell = relationship('Cell', foreign_keys='Order.receiving_cell_id', lazy=True, uselist=False)

print("Order model created successfully.")