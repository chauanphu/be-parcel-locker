from sqlalchemy import Column, Integer, String, Sequence, VARCHAR
from database.__init__ import Base

# TABLE_ID = Sequence('table_id_seq', start=1000)

class User(Base):
    """
    Represents a user in the system.
    """
    __tablename__ = 'user'
    
    # user_id = Column(Integer, TABLE_ID, primary_key=True, server_default=TABLE_ID.next_value())
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    username = Column(VARCHAR(20), nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    password = Column(String)

print("User model created successfully.")