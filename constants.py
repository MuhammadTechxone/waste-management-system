"""
Centralized mapping for severity scores and state transitions (Spec Sections 3.1 & 9.1).
"""

SEVERITY_SCORES = {
    "Low": 20,
    "Medium": 50,
    "High": 80,
    "Critical": 100
}

STATE_TRANSITIONS = {
    "reported": {"verified", "rejected", "expired"},
    "verified": {"investigating", "rejected"},
    "investigating": {"assigned", "rejected"},
    "assigned": {"resolved", "investigating"},
    "resolved": set(), "rejected": set(), "expired": set()
}