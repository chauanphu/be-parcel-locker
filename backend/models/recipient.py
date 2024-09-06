from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from database.__init__ import Base

class Recipient(Base):
    
    __tablename__ = 'recipient'
    
    recipient_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    profile_id = Column(Integer,ForeignKey('profile.user_id') ,index=True,nullable=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    address = Column(String, nullable=True)
    gender = Column(Enum('Male', 'Female', 'Prefer not to respond', name='gender'))
    
print("Recipient model created successfully.")