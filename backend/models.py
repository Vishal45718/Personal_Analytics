from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean, BigInteger, TIMESTAMP, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    timezone = Column(String(50), default='UTC')
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    date = Column(Date, nullable=False)
    sleep_start = Column(DateTime)
    sleep_end = Column(DateTime)
    sleep_duration_min = Column(Integer)
    sleep_quality = Column(Integer)  # 1-5 self-reported or wearable
    deep_sleep_pct = Column(Float)
    mood_score = Column(Integer)  # 1-5 morning mood
    notes = Column(Text)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    sessions = relationship("ActivitySession", back_populates="log")
    __table_args__ = ({'sqlite_autoincrement': True},)

class ActivitySession(Base):
    __tablename__ = "activity_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    started_at = Column(TIMESTAMP, nullable=False)
    ended_at = Column(TIMESTAMP, nullable=False)
    duration_seconds = Column(Integer)
    app_name = Column(String(255))
    window_title = Column(Text)
    category = Column(String(50))  # 'code', 'social_media', 'video_streaming', etc.
    is_distraction = Column(Boolean, default=False)
    focus_depth_score = Column(Float)  # 0-10, computed post-session
    source = Column(String(50))  # 'manual', 'browser_ext', 'desktop_agent'
    log_id = Column(Integer, ForeignKey("daily_logs.id"))

    log = relationship("DailyLog", back_populates="sessions")
    __table_args__ = ({'sqlite_autoincrement': True},)

class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    generated_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    severity = Column(String(20))  # 'info', 'warning', 'critical'
    category = Column(String(50))  # 'sleep', 'productivity', 'burnout', 'pattern'
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    data_json = Column(JSON)  # raw supporting numbers
