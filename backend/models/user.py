from sqlalchemy import Column, Integer, String, VARCHAR
from database.__init__ import Base

class User(Base):
    """
    Represents a user in the system.
    """
    __tablename__ = 'user'
    
    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    username = Column(VARCHAR(20), nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    password = Column(String)

print("User model created successfully.")