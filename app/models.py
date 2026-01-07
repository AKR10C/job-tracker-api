from sqlalchemy import Column, Integer,String, ForeignKey
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(225))

class job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    company = Column(String(100))
    status = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id"))