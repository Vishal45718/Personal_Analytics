from datetime import date, timedelta, datetime
import random
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models

models.Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    if db.query(models.DailyLog).first():
        print("Database already seeded.")
        return
        
    today = date.today()
    for i in range(14, -1, -1):
        d = today - timedelta(days=i)
        
        sleep = random.uniform(4.5, 8.5)
        # Bad sleep impacts productivity randomly
        if sleep < 6:
            prod = random.randint(30, 60)
            coding = random.randint(60, 180)
            mood = random.randint(1, 3)
            distraction = random.randint(120, 240)
        else:
            prod = random.randint(65, 95)
            coding = random.randint(180, 400)
            mood = random.randint(3, 5)
            distraction = random.randint(30, 90)
            
        log = models.DailyLog(
            date=d,
            sleep_hours=round(sleep, 1),
            mood_score=mood,
            total_coding_minutes=coding,
            productivity_score=prod
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        # Add distaction session
        if distraction > 0:
            s_d = models.ActivitySession(
                category="Distraction",
                app_name="YouTube",
                duration_minutes=distraction,
                log_id=log.id,
                start_time=datetime.combine(d, datetime.min.time())
            )
            db.add(s_d)
            
        # Add coding session
        if coding > 0:
            s_c = models.ActivitySession(
                category="Coding",
                app_name="VSCode",
                duration_minutes=coding,
                log_id=log.id,
                start_time=datetime.combine(d, datetime.min.time())
            )
            db.add(s_c)
    db.commit()
    print("Database seeded with 14 days of 'honest' data!")
    db.close()

if __name__ == "__main__":
    seed()
