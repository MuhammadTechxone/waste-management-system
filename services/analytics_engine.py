from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from models import Report
from .clustering import cluster_reports

def get_dashboard_stats(db: Session):
    """Computes all metrics defined in Spec Section 8.1."""
    now = datetime.utcnow()
    last_30d = now - timedelta(days=30)
    last_90d = now - timedelta(days=90)

    # 1. Unresolved count
    unresolved = db.query(Report).filter(
        ~Report.state.in_(["resolved", "rejected", "expired"])
    ).count()

    # 2. Cleanup Efficiency (%) - Last 30 days
    resolved_count = db.query(Report).filter(Report.state == "resolved", Report.updated_at >= last_30d).count()
    terminal_count = db.query(Report).filter(
        Report.state.in_(["resolved", "expired", "rejected"]),
        Report.updated_at >= last_30d
    ).count()
    efficiency = (resolved_count / terminal_count * 100) if terminal_count > 0 else 0

    # 3. Avg resolve days - Last 90 days
    resolved_reports = db.query(Report).filter(Report.state == "resolved", Report.updated_at >= last_90d).all()
    avg_days = 0
    if resolved_reports:
        total_days = sum((r.updated_at - r.created_at).total_seconds() / 86400 for r in resolved_reports)
        avg_days = total_days / len(resolved_reports)

    # 4. Severity distribution (Active reports)
    active_reports = db.query(Report).filter(~Report.state.in_(["resolved", "rejected", "expired"])).all()
    severity_dist = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    if active_reports:
        for r in active_reports:
            if r.severity in severity_dist:
                severity_dist[r.severity] += 1
        for k in severity_dist:
            severity_dist[k] = round((severity_dist[k] / len(active_reports)) * 100, 1)

    # 5. Daily Frequency (last 30 days)
    daily_stats = db.query(
        func.date(Report.created_at).label("date"),
        func.count(Report.id).label("count")
    ).filter(Report.created_at >= last_30d).group_by("date").all()
    
    # 6. Top areas (Clustering)
    clusters = cluster_reports(active_reports)
    for c in clusters:
        c["score"] = c["size"] * c["max_severity"]
    
    top_areas = sorted(clusters, key=lambda x: x["score"], reverse=True)[:10]

    return {
        "generated_at": now.isoformat(),
        "unresolved_count": unresolved,
        "cleanup_efficiency_pct": round(efficiency, 1),
        "avg_resolve_days": round(avg_days, 1),
        "severity_distribution": severity_dist,
        "daily_frequency": [{"date": str(d.date), "count": d.count} for d in daily_stats],
        "top_areas": top_areas
    }