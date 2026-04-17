import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import DailyLog, ActivitySession, Insight
from typing import List, Dict, Any

def calculate_wasted_time(user_id: int, db: Session, days: int = 7) -> dict:
    """
    Returns daily wasted time in minutes for the last N days.
    'Wasted' = sessions labeled distraction OR sessions in
    low-value app categories under 10-minute fragments.
    """
    cutoff = datetime.now() - timedelta(days=days)

    sessions = db.query(ActivitySession).filter(
        ActivitySession.user_id == user_id,
        ActivitySession.started_at >= cutoff
    ).all()

    # Group by date
    daily_data = {}
    for s in sessions:
        date_key = s.started_at.date().isoformat()
        if date_key not in daily_data:
            daily_data[date_key] = {'total_min': 0, 'wasted_min': 0}

        duration_min = s.duration_seconds / 60
        daily_data[date_key]['total_min'] += duration_min

        # Mark wasted: explicit distraction flag OR social/video category
        LOW_VALUE = {'social_media', 'video_streaming', 'messaging'}
        if s.is_distraction or s.category in LOW_VALUE:
            daily_data[date_key]['wasted_min'] += duration_min

    # Calculate waste percentages and averages
    total_wasted = 0
    count = 0
    for day_data in daily_data.values():
        if day_data['total_min'] > 0:
            day_data['waste_pct'] = round(day_data['wasted_min'] / day_data['total_min'] * 100, 1)
        else:
            day_data['waste_pct'] = 0
        total_wasted += day_data['wasted_min']
        count += 1

    avg_wasted = total_wasted / count if count > 0 else 0

    return {
        "daily_wasted": daily_data,
        "avg_wasted_min": round(avg_wasted, 1),
        "human_readable": f"~{round(avg_wasted / 60, 1)}h/day on low-value activities"
    }

def detect_late_night_productivity_drop(user_id: int, db: Session) -> dict:
    """
    Detects if sessions after 11PM consistently have lower focus depth.
    Returns pattern data if found.
    """
    sessions = db.query(ActivitySession).filter(
        ActivitySession.user_id == user_id,
        ActivitySession.category == 'code'
    ).all()

    if len(sessions) < 14:
        return {"pattern_found": False}

    late_scores = []
    prime_scores = []

    for s in sessions:
        focus_score = s.focus_depth_score or 5.0
        if s.started_at.hour >= 23:
            late_scores.append(focus_score)
        elif 9 <= s.started_at.hour < 18:
            prime_scores.append(focus_score)

    if not late_scores or not prime_scores:
        return {"pattern_found": False}

    late_avg = sum(late_scores) / len(late_scores)
    prime_avg = sum(prime_scores) / len(prime_scores)

    drop_pct = round((prime_avg - late_avg) / prime_avg * 100, 1) if prime_avg > 0 else 0

    return {
        "pattern_found": drop_pct > 20,
        "late_night_avg": round(late_avg, 2),
        "prime_hours_avg": round(prime_avg, 2),
        "drop_percent": drop_pct,
        "insight": f"Your focus depth drops {drop_pct}% after 11 PM vs your 9-5 window"
    }

def calculate_sleep_debt_impact(user_id: int, db: Session) -> dict:
    """Calculate how poor sleep affects productivity"""
    logs = db.query(DailyLog).filter(
        DailyLog.user_id == user_id
    ).order_by(DailyLog.date.desc()).limit(30).all()

    if len(logs) < 7:
        return {"pattern_found": False}

    bad_sleep_logs = []
    good_sleep_logs = []

    for log in logs:
        sleep_min = log.sleep_duration_min or 0
        if sleep_min < 360:  # < 6 hours
            bad_sleep_logs.append(log)
        else:
            good_sleep_logs.append(log)

    if not bad_sleep_logs or not good_sleep_logs:
        return {"pattern_found": False}

    # Calculate productivity for each group
    def get_productivity(log):
        # Get coding sessions for this log's date
        sessions = db.query(ActivitySession).filter(
            ActivitySession.log_id == log.id,
            ActivitySession.category == 'code'
        ).all()
        coding_min = sum(s.duration_seconds for s in sessions) / 60
        return min(100, coding_min * 0.5)  # rough calculation

    good_productivities = [get_productivity(log) for log in good_sleep_logs]
    bad_productivities = [get_productivity(log) for log in bad_sleep_logs]

    good_avg = sum(good_productivities) / len(good_productivities)
    bad_avg = sum(bad_productivities) / len(bad_productivities)

    impact = good_avg - bad_avg

    return {
        "pattern_found": impact > 10,
        "impact_pct": round(impact, 1),
        "avg_good_sleep_prod": round(good_avg, 1),
        "avg_bad_sleep_prod": round(bad_avg, 1)
    }

def get_insights(user_id: int, db: Session) -> List[Dict[str, Any]]:
    """Main insight generation function"""
    insights = []

    # Wasted time insight
    wasted = calculate_wasted_time(user_id, db)
    if wasted['avg_wasted_min'] > 120:
        insights.append({
            "id": "wasted_time_high",
            "severity": "critical",
            "category": "productivity",
            "title": "You're hemorrhaging 2+ hours/day",
            "body": f"You average {round(wasted['avg_wasted_min']/60, 1)}h/day on low-value activity. Over 30 days that's {round(wasted['avg_wasted_min']/60*30)} hours — almost 4 full work weeks.",
            "data": wasted
        })

    # Late night productivity drop
    late_drop = detect_late_night_productivity_drop(user_id, db)
    if late_drop['pattern_found']:
        insights.append({
            "id": "late_productivity_drop",
            "severity": "warning",
            "category": "sleep",
            "title": "Post-11PM work is mostly theater",
            "body": late_drop['insight'],
            "data": late_drop
        })

    # Sleep debt impact
    sleep_impact = calculate_sleep_debt_impact(user_id, db)
    if sleep_impact['pattern_found']:
        insights.append({
            "id": "sleep_debt_compounding",
            "severity": "critical",
            "category": "sleep",
            "title": "Chronic sleep debt detected",
            "body": f"Poor sleep is costing you {sleep_impact['impact_pct']}% productivity. Your output drops from {sleep_impact['avg_good_sleep_prod']} to {sleep_impact['avg_bad_sleep_prod']} after bad nights.",
            "data": sleep_impact
        })

    # Sort by severity
    order = {"critical": 0, "warning": 1, "info": 2}
    insights.sort(key=lambda x: order.get(x["severity"], 3))

    return insights

def refresh_insights(user_id: int, db: Session):
    """Generate and store insights in database"""
    insights = get_insights(user_id, db)

    # Clear old insights
    db.query(Insight).filter(Insight.user_id == user_id).delete()

    # Store new ones
    for insight in insights:
        db_insight = Insight(
            user_id=user_id,
            severity=insight['severity'],
            category=insight['category'],
            title=insight['title'],
            body=insight['body'],
            data_json=json.dumps(insight.get('data', {}))
        )
        db.add(db_insight)

    db.commit()

def get_stored_insights(user_id: int, db: Session) -> List[Dict[str, Any]]:
    """Get insights from database"""
    insights = db.query(Insight).filter(
        Insight.user_id == user_id
    ).order_by(Insight.generated_at.desc()).all()

    return [{
        "id": i.id,
        "severity": i.severity,
        "category": i.category,
        "title": i.title,
        "body": i.body,
        "data": json.loads(i.data_json) if i.data_json else {}
    } for i in insights]

def detect_late_night_productivity_drop(user_id: int, db: Session) -> dict:
    """
    Detects if sessions after 11PM consistently have lower focus depth.
    Returns pattern data if found.
    """
    sessions = db.query(ActivitySession).filter(
        ActivitySession.user_id == user_id,
        ActivitySession.category == 'code'
    ).all()

    df = pd.DataFrame([{
        'hour': s.started_at.hour,
        'focus_depth': s.focus_depth_score or 5.0,  # default if None
        'duration_min': s.duration_seconds / 60
    } for s in sessions])

    if len(df) < 14:
        return {"pattern_found": False}

    late = df[df['hour'] >= 23]['focus_depth'].mean()
    prime = df[(df['hour'] >= 9) & (df['hour'] < 18)]['focus_depth'].mean()

    drop_pct = round((prime - late) / prime * 100, 1) if prime > 0 else 0

    return {
        "pattern_found": drop_pct > 20,
        "late_night_avg": round(late, 2),
        "prime_hours_avg": round(prime, 2),
        "drop_percent": drop_pct,
        "insight": f"Your focus depth drops {drop_pct}% after 11 PM vs your 9-5 window"
    }

def calculate_sleep_debt_impact(user_id: int, db: Session) -> dict:
    """Calculate how poor sleep affects productivity"""
    logs = db.query(DailyLog).filter(
        DailyLog.user_id == user_id
    ).order_by(DailyLog.date.desc()).limit(30).all()

    if len(logs) < 7:
        return {"pattern_found": False}

    df = pd.DataFrame([{
        'date': log.date,
        'sleep_min': log.sleep_duration_min or (log.sleep_hours * 60 if log.sleep_hours else 0),
        'mood': log.mood_score,
        'productivity': 50  # placeholder - need to calculate from sessions
    } for log in logs])

    # Calculate productivity from coding sessions
    for idx, row in df.iterrows():
        day_sessions = db.query(ActivitySession).filter(
            ActivitySession.user_id == user_id,
            ActivitySession.started_at >= datetime.combine(row['date'], datetime.min.time()),
            ActivitySession.started_at < datetime.combine(row['date'] + timedelta(days=1), datetime.min.time()),
            ActivitySession.category == 'code'
        ).all()
        coding_min = sum(s.duration_seconds for s in day_sessions) / 60
        df.at[idx, 'productivity'] = min(100, coding_min * 0.5)  # rough calculation

    bad_sleep = df[df['sleep_min'] < 360]  # < 6 hours
    good_sleep = df[df['sleep_min'] >= 360]

    if bad_sleep.empty or good_sleep.empty:
        return {"pattern_found": False}

    impact = good_sleep['productivity'].mean() - bad_sleep['productivity'].mean()

    return {
        "pattern_found": impact > 10,
        "impact_pct": round(impact, 1),
        "avg_good_sleep_prod": round(good_sleep['productivity'].mean(), 1),
        "avg_bad_sleep_prod": round(bad_sleep['productivity'].mean(), 1)
    }

def get_insights(user_id: int, db: Session) -> List[Dict[str, Any]]:
    """Main insight generation function"""
    insights = []

    # Wasted time insight
    wasted = calculate_wasted_time(user_id, db)
    if wasted['avg_wasted_min'] > 120:
        insights.append({
            "id": "wasted_time_high",
            "severity": "critical",
            "category": "productivity",
            "title": "You're hemorrhaging 2+ hours/day",
            "body": f"You average {round(wasted['avg_wasted_min']/60, 1)}h/day on low-value activity. Over 30 days that's {round(wasted['avg_wasted_min']/60*30)} hours — almost 4 full work weeks.",
            "data": wasted
        })

    # Late night productivity drop
    late_drop = detect_late_night_productivity_drop(user_id, db)
    if late_drop['pattern_found']:
        insights.append({
            "id": "late_productivity_drop",
            "severity": "warning",
            "category": "sleep",
            "title": "Post-11PM work is mostly theater",
            "body": late_drop['insight'],
            "data": late_drop
        })

    # Sleep debt impact
    sleep_impact = calculate_sleep_debt_impact(user_id, db)
    if sleep_impact['pattern_found']:
        insights.append({
            "id": "sleep_debt_compounding",
            "severity": "critical",
            "category": "sleep",
            "title": "Chronic sleep debt detected",
            "body": f"Poor sleep is costing you {sleep_impact['impact_pct']}% productivity. Your output drops from {sleep_impact['avg_good_sleep_prod']} to {sleep_impact['avg_bad_sleep_prod']} after bad nights.",
            "data": sleep_impact
        })

    # Sort by severity
    order = {"critical": 0, "warning": 1, "info": 2}
    insights.sort(key=lambda x: order.get(x["severity"], 3))

    return insights

def refresh_insights(user_id: int, db: Session):
    """Generate and store insights in database"""
    insights = get_insights(user_id, db)

    # Clear old insights
    db.query(Insight).filter(Insight.user_id == user_id).delete()

    # Store new ones
    for insight in insights:
        db_insight = Insight(
            user_id=user_id,
            severity=insight['severity'],
            category=insight['category'],
            title=insight['title'],
            body=insight['body'],
            data_json=json.dumps(insight.get('data', {}))
        )
        db.add(db_insight)

    db.commit()

def get_stored_insights(user_id: int, db: Session) -> List[Dict[str, Any]]:
    """Get insights from database"""
    insights = db.query(Insight).filter(
        Insight.user_id == user_id
    ).order_by(Insight.generated_at.desc()).all()

    return [{
        "id": i.id,
        "severity": i.severity,
        "category": i.category,
        "title": i.title,
        "body": i.body,
        "data": json.loads(i.data_json) if i.data_json else {}
    } for i in insights]
