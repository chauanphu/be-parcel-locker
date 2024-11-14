from sqlalchemy import Column,Integer, String, Enum as SQLEnum, ForeignKey
from database.__init__ import Base
from enum import Enum

class GenderEnum(Enum):
    Male = "Male",
    Female = "Female",
    PREFER_NOT_TO_RESPOND = "Prefer not to respond"

class Profile(Base):
    """
    Represents profile of a user in the system.
    """
    __tablename__ = 'profile'
    
    user_id = Column(Integer, ForeignKey('account.user_id'), primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    gender = Column(SQLEnum(GenderEnum, name="gender_profile"), nullable = False, default=GenderEnum.PREFER_NOT_TO_RESPOND)
    age = Column(Integer, nullable = False)
    phone = Column(String, nullable = False)
    address = Column(String, nullable = False)
print("Profile model created successfully.")