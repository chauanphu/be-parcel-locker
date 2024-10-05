from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from database.__init__ import Base

class Shipper(Base):
    """
    Represents profile of a user in the system.
    """
    __tablename__ = 'shipper'

    shipper_id = Column(Integer, ForeignKey('profile.user_id'), primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('order.order_id'),primary_key= True)
    name = Column(String)
    gender = Column(Enum('Male', 'Female', 'Prefer not to respond', name='gender_shipper'))
    age = Column(Integer)
    phone = Column(String, nullable = False)
    address = Column(String, nullable = False)

print("Shipper model created successfully.")