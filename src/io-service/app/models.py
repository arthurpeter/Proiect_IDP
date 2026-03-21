from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    email_logs = relationship("EmailLog", back_populates="user", cascade="all, delete-orphan")

class EmailLog(Base):
    __tablename__ = "email_logs"
    id = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient = Column(String, nullable=False)
    subject = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
    scheduled_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="email_logs")

    