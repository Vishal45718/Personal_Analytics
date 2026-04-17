from datetime import date, timedelta, datetime, time
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

    # Create default user
    user = models.User(email="user@example.com", timezone="UTC")
    db.add(user)
    db.commit()

    today = date.today()
    for i in range(14, -1, -1):
        d = today - timedelta(days=i)

        # Generate realistic sleep data
        sleep_hours = random.uniform(4.5, 8.5)
        sleep_min = int(sleep_hours * 60)
        sleep_quality = random.randint(1, 5)
        deep_sleep_pct = random.uniform(15, 25) if sleep_quality >= 3 else random.uniform(5, 15)

        # Mood correlates with sleep
        if sleep_hours < 6:
            mood = random.randint(1, 3)
        else:
            mood = random.randint(3, 5)

        # Generate sleep times
        sleep_start = datetime.combine(d - timedelta(days=1), time(hour=random.randint(22, 23), minute=random.randint(0, 59)))
        sleep_end = sleep_start + timedelta(minutes=sleep_min)

        log = models.DailyLog(
            user_id=user.id,
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

        # Generate activity sessions
        sessions_data = []

        # Coding sessions
        coding_min = random.randint(60, 400) if sleep_hours >= 6 else random.randint(30, 150)
        if coding_min > 0:
            # Split into 2-4 sessions throughout the day
            remaining = coding_min
            session_count = random.randint(2, 4)
            for j in range(session_count):
                if remaining <= 0:
                    break
                duration = min(remaining, random.randint(30, 120))
                start_hour = random.randint(9, 18)
                start_time = datetime.combine(d, time(hour=start_hour, minute=random.randint(0, 59)))
                end_time = start_time + timedelta(minutes=duration)

                sessions_data.append({
                    'category': 'code',
                    'app_name': random.choice(['VSCode', 'PyCharm', 'IntelliJ', 'Sublime Text']),
                    'duration_seconds': duration * 60,
                    'started_at': start_time,
                    'ended_at': end_time,
                    'is_distraction': False,
                    'focus_depth_score': random.uniform(6, 10) if sleep_hours >= 6 else random.uniform(3, 7),
                    'source': 'desktop_agent'
                })
                remaining -= duration

        # Distraction sessions
        distraction_min = random.randint(30, 180)
        if distraction_min > 0:
            start_hour = random.randint(10, 20)
            start_time = datetime.combine(d, time(hour=start_hour, minute=random.randint(0, 59)))
            end_time = start_time + timedelta(minutes=distraction_min)

            sessions_data.append({
                'category': random.choice(['social_media', 'video_streaming', 'messaging']),
                'app_name': random.choice(['YouTube', 'Twitter', 'Reddit', 'Slack', 'Discord']),
                'duration_seconds': distraction_min * 60,
                'started_at': start_time,
                'ended_at': end_time,
                'is_distraction': True,
                'focus_depth_score': random.uniform(1, 4),
                'source': 'desktop_agent'
            })

        # Add sessions to database
        for s_data in sessions_data:
            s = models.ActivitySession(
                user_id=user.id,
                category=s_data['category'],
                app_name=s_data['app_name'],
                duration_seconds=s_data['duration_seconds'],
                started_at=s_data['started_at'],
                ended_at=s_data['ended_at'],
                is_distraction=s_data['is_distraction'],
                focus_depth_score=s_data['focus_depth_score'],
                source=s_data['source'],
                log_id=log.id
            )
            db.add(s)

    db.commit()

    # Generate initial insights
    from analytics import refresh_insights
    refresh_insights(user.id, db)

    print("Database seeded with 15 days of realistic data!")
    db.close()

if __name__ == "__main__":
    seed()
