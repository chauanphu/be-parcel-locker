from sqlalchemy import Column, Integer, String, Sequence, VARCHAR,Enum,DateTime
from database.__init__ import Base
from datetime import datetime

class Account(Base):

    __tablename__ = 'account'
    
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, nullable=False)
    username = Column(VARCHAR(20), nullable=False)
    password = Column(String,nullable=False)
    status = Column(Enum('Active','Inactive', 'Blocked', name='status'), nullable=False,default='Active')
    Date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    role = Column(Integer, nullable=False, default=2)

    
print("Account model created successfully.")