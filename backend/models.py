from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False)
    sleep_hours = Column(Float)
    mood_score = Column(Integer) # 1-5
    total_coding_minutes = Column(Integer)
    productivity_score = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sessions = relationship("ActivitySession", back_populates="log")

class ActivitySession(Base):
    __tablename__ = "activity_sessions"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50)) # 'Coding', 'Distraction', 'Generic'
    app_name = Column(String(100))
    duration_minutes = Column(Integer)
    log_id = Column(Integer, ForeignKey("daily_logs.id"))
    start_time = Column(DateTime)

    log = relationship("DailyLog", back_populates="sessions")
