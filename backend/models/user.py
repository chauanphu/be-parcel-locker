import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, VARCHAR
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from database.__init__ import Base

# TABLE_ID = Sequence('table_id_seq', start=1000)

class Role(Base):
    """
    Represents a role in the system.
    """
    __tablename__ = 'role'
    
    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, nullable=False)

class Account(Base):
    """
    Represents an account in the system.
    """
    __tablename__ = 'account'
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username= Column(VARCHAR(20), nullable=False, unique=True)
    # Create email with validation for valid email, and unique constraint
    email = Column(String, nullable=False, unique=True)
    password = Column(String(), nullable=False)
    role_id = Column(Integer,  ForeignKey('role.role_id'), nullable=False)
    
    role = relationship('Role', backref='account', lazy=True, foreign_keys=[role_id], uselist=False)

class Profile(Base):
    """
    Represents a profile in the system.
    """
    __tablename__ = 'profile'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("account.user_id"), primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    
    account = relationship('Account', backref='profile', lazy=True, foreign_keys=[user_id], uselist=False)