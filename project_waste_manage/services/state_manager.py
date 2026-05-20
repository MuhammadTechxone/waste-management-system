from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Report
from constants import STATE_TRANSITIONS

def validate_and_update_state(db: Session, report: Report, new_state: str):
    """
    Validates the state transition and updates the report (Spec Section 3.1 & 3.2).
    """
    allowed_next_states = STATE_TRANSITIONS.get(report.state, set())
    
    if new_state not in allowed_next_states:
        raise ValueError(
            f"Invalid transition from '{report.state}' to '{new_state}'. "
            f"Allowed states: {list(allowed_next_states)}"
        )

    report.state = new_state
    report.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(report)
    return report

EXPIRY_DAYS = 30
EXPIRY_ELIGIBLE = {"reported", "verified"}

def expire_stale_reports(db: Session):
    cutoff = datetime.utcnow() - timedelta(days=EXPIRY_DAYS)
    stale = db.query(Report).filter(
        Report.state.in_(EXPIRY_ELIGIBLE),
        Report.created_at < cutoff
    ).all()
    
    for r in stale:
        r.state = "expired"
        r.updated_at = datetime.utcnow()
    
    db.commit()
    return len(stale)