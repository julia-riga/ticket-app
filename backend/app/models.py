from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum
from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class StatusEnum(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    done = "done"

class PriorityEnum(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(120), nullable=False)
    description = Column(String(1000), nullable=True)
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.new, nullable=False)
    priority = Column(SQLEnum(PriorityEnum), default=PriorityEnum.normal, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # default/onupdate на стороне Python, чтобы значение было заполнено
    # и для баз, созданных до появления этих полей в модели
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)