from sqlalchemy import Column, Integer, String
from database.__init__ import Base


class Role(Base):
    """
    Represents a role in the system.
    """

    __tablename__ = 'role'
    
    role_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    