from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)  # 기본키
    email = Column(String, unique=True, index=True, nullable=False) # 고유키
    name = Column(String, nullable=True)
    social_provider = Column(String, nullable=False, index=True)
    social_id = Column(String, nullable=False, index=True, unique=True) # 고유키
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
