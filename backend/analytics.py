from sqlalchemy.orm import Session
from models import DailyLog, ActivitySession

class InsightEngine:
    def __init__(self, logs):
        self.logs = logs

    def calculate_sleep_debt_impact(self):
        if not self.logs or len(self.logs) < 2:
            return None
            
        bad_sleep_scores = [log.productivity_score for log in self.logs if log.sleep_hours < 6.0]
        normal_sleep_scores = [log.productivity_score for log in self.logs if log.sleep_hours >= 6.0]
        
        if not bad_sleep_scores or not normal_sleep_scores:
            return None
            
        normal_avg = sum(normal_sleep_scores) / len(normal_sleep_scores)
        bad_avg = sum(bad_sleep_scores) / len(bad_sleep_scores)
        
        impact = normal_avg - bad_avg
        
        if impact > 15:
            return {
                "level": "CRITICAL",
                "message": f"Poor sleep is killing your output. You ship {impact:.1f}% less code after late nights."
            }
        return None

    def detect_wasted_time(self, sessions):
        if not sessions:
            return None
        distractions = sum([s.duration_minutes for s in sessions if s.category == 'Distraction'])
        if distractions > 120:
            return {
                "level": "WARNING",
                "message": f"You spent {distractions/60:.1f} hours on distractions recently. That's a 'death by a thousand tabs' reality."
            }
        return None
        
    def overall_vibe_check(self):
        if not self.logs: return None
        recent_log = self.logs[-1]
        score = recent_log.productivity_score
        if score < 40:
             return {"level": "CRITICAL", "message": "Absolutely zero momentum. Are you even trying?"}
        elif score > 85:
             return {"level": "INFO", "message": "High output. Don't let it fool you, burnout is a few days away."}
        return None

def predict_tomorrow_efficiency(logs):
    if len(logs) < 3:
        return 50 # Default if not enough data
        
    # Simple weighted moving average for trend prediction
    weights = [0.2, 0.3, 0.5]
    recent = logs[-3:]
    trend = sum([l.productivity_score * w for l, w in zip(recent, weights)])
    return max(0, min(100, float(trend)))

def get_insights(db: Session):
    logs = db.query(DailyLog).order_by(DailyLog.date.asc()).all()
    sessions_today = []
    if logs:
        last_log = logs[-1]
        sessions_today = db.query(ActivitySession).filter(ActivitySession.log_id == last_log.id).all()
        
    if not logs:
        return {"insights": [], "tomorrow_prediction": 50}
        
    engine = InsightEngine(logs)
    sleep_insight = engine.calculate_sleep_debt_impact()
    distraction_insight = engine.detect_wasted_time(sessions_today)
    vibe_insight = engine.overall_vibe_check()
    
    insights = [i for i in [sleep_insight, distraction_insight, vibe_insight] if i is not None]
    
    prediction = predict_tomorrow_efficiency(logs)
    
    return {
        "insights": insights,
        "tomorrow_prediction": round(prediction)
    }
