from sqlalchemy import Column, Integer, String, VARCHAR
from database.__init__ import Base

class User(Base):
    __tablename__ = 'user'

    email = Column(String, primary_key=True)
    username = Column(VARCHAR(20),nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    password = Column(String)
