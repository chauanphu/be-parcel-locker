from sqlalchemy import Column, Integer, String, Sequence, VARCHAR,Enum,DateTime
from database.__init__ import Base
from datetime import datetime

# TABLE_ID = Sequence('table_id_seq', start=1000)

class User(Base):
    """
    Represents a user in the system.
    """
    __tablename__ = 'user'
    
    # user_id = Column(Integer, TABLE_ID, primary_key=True, server_default=TABLE_ID.next_value())
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, primary_key=True)
    name = Column(String)
    username = Column(VARCHAR(20), nullable=False)
    address = Column(String)
    phone = Column(String)
    password = Column(String,nullable=False)
    status = Column(Enum('Active','Inactive', 'Blocked', name='status'), nullable=False,default='Active')
    Date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    role = Column(Integer, nullable=False, default=2)

    
print("User model created successfully.")