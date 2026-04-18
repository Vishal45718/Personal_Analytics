from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi import Request
from fastapi_sso.sso.github import GithubSSO
from fastapi_sso.sso.google import GoogleSSO
from auth import create_access_token, get_current_user

import models
from database import engine, SessionLocal
import analytics

models.Base.metadata.create_all(bind=engine)

import os

app = FastAPI()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

github_sso = GithubSSO(GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, "http://localhost:8000/api/auth/github/callback", allow_insecure_http=True)
google_sso = GoogleSSO(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, "http://localhost:8000/api/auth/google/callback", allow_insecure_http=True)

# Allow frontend to connect securely
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

@app.get("/api/auth/{provider}/login")
async def auth_login(provider: str):
    if provider == "github":
        with github_sso:
            return await github_sso.get_login_redirect()
    elif provider == "google":
        with google_sso:
            return await google_sso.get_login_redirect()
    raise HTTPException(status_code=404, detail="Provider not found")

@app.get("/api/auth/{provider}/callback")
async def auth_callback(provider: str, request: Request, db: Session = Depends(get_db)):
    if provider == "github":
        with github_sso:
            user_info = await github_sso.verify_and_process(request)
    elif provider == "google":
        with google_sso:
            user_info = await google_sso.verify_and_process(request)
    else:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    user = db.query(models.User).filter(models.User.provider == provider, models.User.provider_id == user_info.id).first()
    if not user:
        user = models.User(
            email=user_info.email,
            name=user_info.display_name,
            avatar=user_info.picture,
            provider=provider,
            provider_id=user_info.id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    access_token = create_access_token(data={"sub": str(user.id)})
    return RedirectResponse(f"{FRONTEND_URL}/login?token={access_token}")

@app.get("/api/users/me")
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "avatar": current_user.avatar
    }

@app.post("/api/logs")
def create_log(log: LogCreate, background_tasks: BackgroundTasks, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if log already exists for this date
    existing = db.query(models.DailyLog).filter(
        models.DailyLog.date == log.date,
        models.DailyLog.user_id == current_user.id
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
        user_id=current_user.id,
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
            user_id=current_user.id,
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
    background_tasks.add_task(analytics.refresh_insights, current_user.id, db)

    return {"message": "Log created successfully", "log_id": db_log.id}

@app.get("/api/logs")
def get_logs(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    logs = db.query(models.DailyLog).options(joinedload(models.DailyLog.sessions)).filter(
        models.DailyLog.user_id == current_user.id
    ).order_by(models.DailyLog.date.desc()).all()

    result = []
    for log in logs:
        sessions = log.sessions

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
def get_insights(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    insights = analytics.get_stored_insights(current_user.id, db)

    # Calculate prediction (simplified)
    logs = db.query(models.DailyLog).filter(
        models.DailyLog.user_id == current_user.id
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
def get_analytics_summary(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get comprehensive analytics summary"""
    user_id = current_user.id

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

@app.post("/api/seed")
def seed_data(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Very simple way to give the user some initial demo data
    from seed import seed as seed_db
    # Modified seed logic for current user
    today = date.today()
    from datetime import timedelta, time
    import random
    
    # check if they already have data
    if db.query(models.DailyLog).filter(models.DailyLog.user_id == current_user.id).first():
        return {"message": "User already has data."}

    for i in range(14, -1, -1):
        d = today - timedelta(days=i)
        sleep_hours = random.uniform(4.5, 8.5)
        sleep_min = int(sleep_hours * 60)
        sleep_quality = random.randint(1, 5)
        deep_sleep_pct = random.uniform(15, 25) if sleep_quality >= 3 else random.uniform(5, 15)
        mood = random.randint(1, 3) if sleep_hours < 6 else random.randint(3, 5)
        sleep_start = datetime.combine(d - timedelta(days=1), time(hour=random.randint(22, 23), minute=random.randint(0, 59)))
        sleep_end = sleep_start + timedelta(minutes=sleep_min)

        log = models.DailyLog(
            user_id=current_user.id,
            date=d,
            sleep_start=sleep_start,
            sleep_end=sleep_end,
            sleep_duration_min=sleep_min,
            sleep_quality=sleep_quality,
            deep_sleep_pct=round(deep_sleep_pct, 1),
            mood_score=mood,
            notes=f"Auto-generated log for {d}"
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        coding_min = random.randint(60, 400) if sleep_hours >= 6 else random.randint(30, 150)
        if coding_min > 0:
            start_time = datetime.combine(d, time(hour=10, minute=0))
            db.add(models.ActivitySession(
                user_id=current_user.id,
                category='code',
                app_name='VSCode',
                duration_seconds=coding_min * 60,
                started_at=start_time,
                ended_at=start_time + timedelta(minutes=coding_min),
                is_distraction=False,
                focus_depth_score=random.uniform(6, 10),
                source='desktop_agent',
                log_id=log.id
            ))
            
        distraction_min = random.randint(30, 180)
        if distraction_min > 0:
            start_time = datetime.combine(d, time(hour=14, minute=0))
            db.add(models.ActivitySession(
                user_id=current_user.id,
                category='social_media',
                app_name='Twitter',
                duration_seconds=distraction_min * 60,
                started_at=start_time,
                ended_at=start_time + timedelta(minutes=distraction_min),
                is_distraction=True,
                focus_depth_score=random.uniform(1, 4),
                source='desktop_agent',
                log_id=log.id
            ))
    db.commit()
    import analytics
    analytics.refresh_insights(current_user.id, db)
    return {"message": "Data seeded successfully"}
