from .verification import haversine_metres

CLUSTER_RADIUS_M = 200
MIN_CLUSTER_SIZE = 3

def cluster_reports(reports: list) -> list:
    """Groups reports into geographic hotspots (Spec Section 7.3)."""
    visited = set()
    clusters = []

    for i, r in enumerate(reports):
        if i in visited:
            continue
        neighbours = [
            j for j, s in enumerate(reports)
            if j != i and
            haversine_metres(r.latitude, r.longitude, s.latitude, s.longitude) <= CLUSTER_RADIUS_M
        ]
        if len(neighbours) + 1 < MIN_CLUSTER_SIZE:
            continue
            
        members = [i] + neighbours
        visited.update(members)
        member_reports = [reports[m] for m in members]
        
        clusters.append({
            "centroid_lat": sum(r.latitude for r in member_reports) / len(member_reports),
            "centroid_lon": sum(r.longitude for r in member_reports) / len(member_reports),
            "report_ids": [r.id for r in member_reports],
            "size": len(member_reports),
            "max_severity": max(r.severity_score for r in member_reports),
        })
    return clusters