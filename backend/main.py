from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
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
    duration_minutes: int
    start_time: str # ISO string

class LogCreate(BaseModel):
    date: date
    sleep_hours: float
    mood_score: int
    total_coding_minutes: int
    productivity_score: int
    sessions: Optional[List[SessionCreate]] = []

@app.post("/api/logs")
def create_log(log: LogCreate, db: Session = Depends(get_db)):
    db_log = db.query(models.DailyLog).filter(models.DailyLog.date == log.date).first()
    if db_log:
        raise HTTPException(status_code=400, detail="Log for this date already exists")
        
    db_log = models.DailyLog(
        date=log.date,
        sleep_hours=log.sleep_hours,
        mood_score=log.mood_score,
        total_coding_minutes=log.total_coding_minutes,
        productivity_score=log.productivity_score,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    for s in log.sessions:
        from datetime import datetime
        try:
            st_time = datetime.fromisoformat(s.start_time.replace('Z', '+00:00'))
        except ValueError:
            st_time = datetime.now() # Fallback
            
        db_s = models.ActivitySession(
            category=s.category,
            app_name=s.app_name,
            duration_minutes=s.duration_minutes,
            start_time=st_time,
            log_id=db_log.id
        )
        db.add(db_s)
    db.commit()
    
    return db_log

@app.get("/api/logs")
def get_logs(db: Session = Depends(get_db)):
    logs = db.query(models.DailyLog).order_by(models.DailyLog.date.asc()).all()
    # Serialize to dict including sessions mapped appropriately if needed
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "date": log.date,
            "sleep_hours": log.sleep_hours,
            "mood_score": log.mood_score,
            "total_coding_minutes": log.total_coding_minutes,
            "productivity_score": log.productivity_score,
        })
    return result

@app.get("/api/insights")
def get_user_insights(db: Session = Depends(get_db)):
    return analytics.get_insights(db)
