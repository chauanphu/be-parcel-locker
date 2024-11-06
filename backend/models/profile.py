from sqlalchemy import Column,Integer, String, Enum, ForeignKey
from database.__init__ import Base

class Profile(Base):
    """
    Represents profile of a user in the system.
    """
    __tablename__ = 'profile'
    
    user_id = Column(Integer, ForeignKey('account.user_id'), primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    gender = Column(Enum('Male', 'Female', 'Prefer not to respond', name='gender_profile'))
    age = Column(Integer)
    phone = Column(String, nullable = False)
    address = Column(String, nullable = False)
print("Profile model created successfully.")