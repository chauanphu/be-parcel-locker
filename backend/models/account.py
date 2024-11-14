from enum import Enum
from sqlalchemy import Column, Integer, String, VARCHAR,Enum as SQLEnum, ForeignKey
from database.__init__ import Base
from sqlalchemy.orm import relationship
from models.role import Role

class GenderEnum(Enum):
    Male = "Male"
    Female = "Female"
    PREFER_NOT_TO_RESPOND = "Prefer not to respond"

class Account(Base):
    """
    Represents account of a user in the system.
    """
    __tablename__ = 'account'
    
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable = False, unique=True, default="")
    username = Column(VARCHAR(20), nullable=False, unique=True)
    name = Column(String, nullable=False, default="")
    password = Column(String,nullable=False)
    gender = Column(SQLEnum(GenderEnum), nullable = False, default=GenderEnum.PREFER_NOT_TO_RESPOND)
    age = Column(Integer, nullable = False, default=0)
    address = Column(String, nullable = False, default="")
    role = Column(Integer,ForeignKey('role.role_id'), nullable=False, default=2)
    role_rel = relationship("Role", back_populates="accounts")

print("Account model created successfully.")