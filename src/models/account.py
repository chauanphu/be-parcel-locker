from sqlalchemy import Column, Integer, String, VARCHAR,Enum,DateTime,ForeignKey
from database.__init__ import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class Account(Base):
    """
    Represents account of a user in the system.
    """
    __tablename__ = 'account'
    
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    username = Column(VARCHAR(20), nullable=False, unique=True)
    password = Column(String,nullable=False)
    status = Column(Enum('Active','Inactive', 'Blocked', name='account_status'), nullable=False,default='Active')
    Date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    role = Column(Integer,ForeignKey('role.role_id'), nullable=False, default=2)
    role_rel = relationship("Role", back_populates="accounts")

    
print("Account model created successfully.")