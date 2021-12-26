from .database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

class Blog(Base):
    __tablename__ = 'blog'
    id=Column(Integer, primary_key=True,index=True)
    title=Column(String)
    body=Column(String)
    
    
class User(Base):
    __tablename__ = 'user'
    id=Column(Integer, primary_key=True,index=True)
    name=Column(String)
    email=Column(String)
    password=Column(String)