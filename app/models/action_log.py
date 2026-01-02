from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_input = Column(String(1000), nullable=False)
    parsed_intent = Column(JSON, nullable=True)
    action_taken = Column(String(255), nullable=True)
    status = Column(String(50), default="pending")
    result = Column(JSON, nullable=True)
    error_message = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
