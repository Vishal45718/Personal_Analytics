from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import models
from database import engine, SessionLocal
import analytics

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SessionCreate(BaseModel):
    category: str
    app_name: str
    duration_seconds: int
    started_at: str  # ISO string
    ended_at: str    # ISO string
    is_distraction: Optional[bool] = False
    focus_depth_score: Optional[float] = None
    source: Optional[str] = 'manual'

class LogCreate(BaseModel):
    date: date
    sleep_start: Optional[str] = None  # ISO string
    sleep_end: Optional[str] = None    # ISO string
    sleep_duration_min: Optional[int] = None
    sleep_quality: Optional[int] = None  # 1-5
    deep_sleep_pct: Optional[float] = None
    mood_score: Optional[int] = None  # 1-5
    notes: Optional[str] = None
    sessions: Optional[List[SessionCreate]] = []

@app.post("/api/logs")
def create_log(log: LogCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Check if log already exists for this date
    existing = db.query(models.DailyLog).filter(
        models.DailyLog.date == log.date,
        models.DailyLog.user_id == 1  # default user
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Log for this date already exists")

    # Parse sleep times
    sleep_start = None
    sleep_end = None
    if log.sleep_start:
        try:
            sleep_start = datetime.fromisoformat(log.sleep_start.replace('Z', '+00:00'))
        except:
            pass
    if log.sleep_end:
        try:
            sleep_end = datetime.fromisoformat(log.sleep_end.replace('Z', '+00:00'))
        except:
            pass

    db_log = models.DailyLog(
        user_id=1,  # default user
        date=log.date,
        sleep_start=sleep_start,
        sleep_end=sleep_end,
        sleep_duration_min=log.sleep_duration_min,
        sleep_quality=log.sleep_quality,
        deep_sleep_pct=log.deep_sleep_pct,
        mood_score=log.mood_score,
        notes=log.notes,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    # Add sessions
    for s in log.sessions:
        try:
            started_at = datetime.fromisoformat(s.started_at.replace('Z', '+00:00'))
            ended_at = datetime.fromisoformat(s.ended_at.replace('Z', '+00:00'))
        except:
            continue  # skip invalid sessions

        db_s = models.ActivitySession(
            user_id=1,
            category=s.category,
            app_name=s.app_name,
            duration_seconds=s.duration_seconds,
            started_at=started_at,
            ended_at=ended_at,
            is_distraction=s.is_distraction,
            focus_depth_score=s.focus_depth_score,
            source=s.source,
            log_id=db_log.id
        )
        db.add(db_s)
    db.commit()

    # Trigger async insight refresh
    background_tasks.add_task(analytics.refresh_insights, 1, db)

    return {"message": "Log created successfully", "log_id": db_log.id}

@app.get("/api/logs")
def get_logs(db: Session = Depends(get_db)):
    logs = db.query(models.DailyLog).filter(
        models.DailyLog.user_id == 1
    ).order_by(models.DailyLog.date.desc()).all()

    result = []
    for log in logs:
        # Get associated sessions
        sessions = db.query(models.ActivitySession).filter(
            models.ActivitySession.log_id == log.id
        ).all()

        result.append({
            "id": log.id,
            "date": log.date.isoformat(),
            "sleep_start": log.sleep_start.isoformat() if log.sleep_start else None,
            "sleep_end": log.sleep_end.isoformat() if log.sleep_end else None,
            "sleep_duration_min": log.sleep_duration_min,
            "sleep_quality": log.sleep_quality,
            "deep_sleep_pct": log.deep_sleep_pct,
            "mood_score": log.mood_score,
            "notes": log.notes,
            "sessions": [{
                "id": s.id,
                "category": s.category,
                "app_name": s.app_name,
                "duration_seconds": s.duration_seconds,
                "started_at": s.started_at.isoformat(),
                "ended_at": s.ended_at.isoformat(),
                "is_distraction": s.is_distraction,
                "focus_depth_score": s.focus_depth_score,
                "source": s.source
            } for s in sessions]
        })
    return result

@app.get("/api/insights")
def get_insights(db: Session = Depends(get_db)):
    insights = analytics.get_stored_insights(1, db)  # default user

    # Calculate prediction (simplified)
    logs = db.query(models.DailyLog).filter(
        models.DailyLog.user_id == 1
    ).order_by(models.DailyLog.date.desc()).limit(7).all()

    prediction = 50  # default
    if logs:
        # Simple prediction based on recent mood and sleep
        recent = logs[0]
        base_score = 50
        if recent.mood_score:
            base_score += (recent.mood_score - 3) * 10
        if recent.sleep_duration_min and recent.sleep_duration_min < 360:
            base_score -= 20
        prediction = max(0, min(100, base_score))

    return {
        "insights": insights,
        "tomorrow_prediction": prediction
    }

@app.get("/api/analytics/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    """Get comprehensive analytics summary"""
    user_id = 1

    # Get last 30 days of logs
    cutoff = datetime.now() - timedelta(days=30)
    logs = db.query(models.DailyLog).filter(
        models.DailyLog.user_id == user_id,
        models.DailyLog.date >= cutoff.date()
    ).order_by(models.DailyLog.date).all()

    # Calculate metrics
    if not logs:
        return {"message": "No data available"}

    # Calculate averages manually
    total_sleep = 0
    total_mood = 0
    total_quality = 0
    count = 0

    for log in logs:
        total_sleep += log.sleep_duration_min or 0
        total_mood += log.mood_score or 3
        total_quality += log.sleep_quality or 3
        count += 1

    avg_sleep = total_sleep / count if count > 0 else 0
    avg_mood = total_mood / count if count > 0 else 3
    avg_quality = total_quality / count if count > 0 else 3

    # Get sessions for productivity calculation
    sessions = db.query(models.ActivitySession).filter(
        models.ActivitySession.user_id == user_id,
        models.ActivitySession.started_at >= cutoff
    ).all()

    # Group sessions by date
    sessions_by_date = {}
    for s in sessions:
        date_key = s.started_at.date()
        if date_key not in sessions_by_date:
            sessions_by_date[date_key] = []
        sessions_by_date[date_key].append(s)

    # Calculate daily productivity
    productivity_data = []
    for log in logs:
        day_sessions = sessions_by_date.get(log.date, [])
        coding_min = sum(s.duration_seconds for s in day_sessions if s.category == 'code') / 60
        distraction_min = sum(s.duration_seconds for s in day_sessions if s.is_distraction) / 60
        total_min = sum(s.duration_seconds for s in day_sessions) / 60

        # Simple productivity score
        productivity = min(100, coding_min * 0.5 - distraction_min * 0.3)
        productivity = max(0, productivity)

        productivity_data.append({
            'date': log.date.isoformat(),
            'productivity_score': round(productivity, 1),
            'coding_minutes': coding_min,
            'distraction_minutes': distraction_min,
            'total_minutes': total_min
        })

    return {
        "logs_summary": {
            "avg_sleep_min": round(avg_sleep),
            "avg_mood": round(avg_mood, 1),
            "avg_sleep_quality": round(avg_quality, 1),
            "total_days": len(logs)
        },
        "productivity_trend": productivity_data,
        "wasted_time": analytics.calculate_wasted_time(user_id, db)
    }
