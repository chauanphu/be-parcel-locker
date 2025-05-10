from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.__init__ import Base


class Role(Base):
    """
    Represents a role in the system.
    """

    __tablename__ = 'role'
    
    role_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    accounts = relationship("Account", back_populates="role_rel")
