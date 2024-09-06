from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Enum, ForeignKey
from database.__init__ import Base

class Profile(Base):
    """
    Represents profile of a user in the system.
    """
    __tablename__ = 'profile'
    
    user_id = Column(Integer, ForeignKey('account.user_id'), primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    # email = Column(String, nullable=False, unique=True)
    gender = Column(Enum('Male', 'Female', 'Prefer not to respond', name='gender'))
    # status = Column(Enum('Active','Inactive', 'Blocked', name='account_status'), nullable=False,default='Active')
    # Date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    age = Column(Integer)
    phone = Column(String, nullable = False)
    address = Column(String, nullable = False)
    #vừa được thêm email, status và Date_created để get paging
print("Profile model created successfully.")