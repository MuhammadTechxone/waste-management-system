# Waste Management System: Engineering & Logic Overview

This document explains the underlying logic of the Waste Management Backend, specifically focusing on the Heatmap generation, Admin Analytics, and the technical terminology used in API communication.

---

## 1. Heatmap Logic (The "Risk Layer")

The Heatmap is the primary tool for public visualization. It does not simply show every report; it shows **Environmental Intensity**.

### Weight Calculation
The `weight` field in the `/heatmap/` response is calculated using:
`Weight = (Severity Score * Confidence Score) / 100`

*   **Severity Influence:** A "Critical" report (100) contributes more weight than a "Low" report (20).
*   **Confidence Influence:** A report with a high-quality image and nearby confirmation is "heavier" than an unverified report.
*   **Temporal Decay:** Reports older than 14 days are excluded by default to ensure the map reflects current ground truth rather than historical data.
*   **Resolution Masking:** Resolved incidents are either hidden or shown at only 10% weight to show that a risk was mitigated.

### Clustering (DBSCAN-lite)
To identify "Hotspots," the system groups reports using a **Radius-Based Grouping** algorithm:
*   **Radius (Epsilon):** 200 meters.
*   **Density Threshold:** Minimum of 3 reports within that radius.
*   **Centroid:** The mathematical center (Average Lat/Lon) of all reports in that group.

---

## 2. Admin Analytics Engine

The analytics engine translates the database into actionable insights for municipal authorities.

| Metric | Logic / Definition | Purpose |
| :--- | :--- | :--- |
| **Cleanup Efficiency** | `(Resolved / (Resolved + Expired + Rejected))` | Measures if the response teams are beating the 30-day "expiry" clock. |
| **Recurring Hotspots** | Clusters appearing in 3+ distinct weeks over 90 days. | Identifies systemic issues (e.g., illegal dumping sites vs. one-time spills). |
| **Avg. Resolve Days** | Time delta between `created_at` and `state = resolved`. | Benchmarks operational speed. |
| **Top Affected Areas** | Ranked by `(Cluster Size * Avg. Severity)`. | Directs resources to the most dangerous zones first. |

---

## 3. Terminology Glossary

### Request Parameters (Inputs)

*   **`min_confidence`**: (Integer 0-100) A filter to remove "noisy" or suspicious reports from the view.
*   **`exclude_resolved`**: (Boolean) When true, removes "Resolved" and "Rejected" reports. Used by citizens who only care about what *needs* cleaning.
*   **`radius_km`**: (Float) Limits results to a circular geographic area. Essential for "Reports Near Me" features.
*   **`is_duplicate`**: (Boolean) Flag used by admins to see reports that hit the 50m/24h threshold or identical image hashes.

### Response Fields (Outputs)

*   **`severity_score`**: An integer mapping of the text labels:
    *   `Low`: 20 | `Medium`: 50 | `High`: 80 | `Critical`: 100
*   **`confidence_score`**: A value from 0-100 representing data reliability.
    *   *Example:* A report starts at 50. Adding a valid image adds +20. Being a duplicate subtracts -25.
*   **`state`**: The operational lifecycle stage:
    *   `reported`: Initial entry.
    *   `verified`: Confirmed by admin or algorithm.
    *   `investigating/assigned`: Operational workflow.
    *   `resolved`: Success state.
    *   `expired`: Cleanup didn't happen in time (30 days).
*   **`image_hash`**: An MD5 fingerprint of the uploaded image. Used to stop users from uploading the same photo multiple times to "spam" a location.

---

## 4. Operational Workflow Summary

1.  **Ingestion:** User submits via `POST /report/`.
2.  **Verification:** The `verification.py` service checks for duplicates and assigns a `confidence_score`.
3.  **Visualization:** The `heatmap_engine.py` processes active reports into weighted JSON for the map.
4.  **Action:** Admins use `PATCH /admin/report/{id}` to move a report through the lifecycle.
5.  **Analytics:** The `analytics_engine.py` runs clustering and frequency analysis to produce the dashboard data.
```

### Overview of Key Concepts

1.  **Separation of Concerns:** Notice that **Severity** (how bad the trash is) and **State** (what we are doing about it) are completely separate. A "Critical" incident remains critical even when it is "Assigned" to a team.
2.  **The 30-Day Rule:** To prevent the database from feeling "cluttered" with old data, the background job in `main.py` (the `auto_expiry_job`) automatically moves reports to the `expired` state if they haven't been resolved within 30 days. This keeps the heatmap fresh.
3.  **Duplicate Handling:** We don't delete duplicates. We store them, but we flag them with `is_duplicate = True`. This allows admins to see that multiple people are complaining about the same thing, which actually *increases* the confidence of the original report.

# Waste Management System: Engineering & Logic Overview

This document explains the underlying logic of the Waste Management Backend, specifically focusing on the Heatmap generation, Admin Analytics, and the technical terminology used in API communication.

---

## 1. Heatmap Logic (The "Risk Layer")

The Heatmap is the primary tool for public visualization. It does not simply show every report; it shows **Environmental Intensity**.

### Weight Calculation
The `weight` field in the `/heatmap/` response is calculated using:
`Weight = (Severity Score * Confidence Score) / 100`

*   **Severity Influence:** A "Critical" report (100) contributes more weight than a "Low" report (20).
*   **Confidence Influence:** A report with a high-quality image and nearby confirmation is "heavier" than an unverified report.
*   **Temporal Decay:** Reports older than 14 days are excluded by default to ensure the map reflects current ground truth rather than historical data.
*   **Resolution Masking:** Resolved incidents are either hidden or shown at only 10% weight to show that a risk was mitigated.

### Clustering (DBSCAN-lite)
To identify "Hotspots," the system groups reports using a **Radius-Based Grouping** algorithm:
*   **Radius (Epsilon):** 200 meters.
*   **Density Threshold:** Minimum of 3 reports within that radius.
*   **Centroid:** The mathematical center (Average Lat/Lon) of all reports in that group.

---

## 2. Admin Analytics Engine

The analytics engine translates the database into actionable insights for municipal authorities.

| Metric | Logic / Definition | Purpose |
| :--- | :--- | :--- |
| **Cleanup Efficiency** | `(Resolved / (Resolved + Expired + Rejected))` | Measures if the response teams are beating the 30-day "expiry" clock. |
| **Recurring Hotspots** | Clusters appearing in 3+ distinct weeks over 90 days. | Identifies systemic issues (e.g., illegal dumping sites vs. one-time spills). |
| **Avg. Resolve Days** | Time delta between `created_at` and `state = resolved`. | Benchmarks operational speed. |
| **Top Affected Areas** | Ranked by `(Cluster Size * Avg. Severity)`. | Directs resources to the most dangerous zones first. |

---

## 3. Terminology Glossary

### Request Parameters (Inputs)

*   **`min_confidence`**: (Integer 0-100) A filter to remove "noisy" or suspicious reports from the view.
*   **`exclude_resolved`**: (Boolean) When true, removes "Resolved" and "Rejected" reports. Used by citizens who only care about what *needs* cleaning.
*   **`radius_km`**: (Float) Limits results to a circular geographic area. Essential for "Reports Near Me" features.
*   **`is_duplicate`**: (Boolean) Flag used by admins to see reports that hit the 50m/24h threshold or identical image hashes.

### Response Fields (Outputs)

*   **`severity_score`**: An integer mapping of the text labels:
    *   `Low`: 20 | `Medium`: 50 | `High`: 80 | `Critical`: 100
*   **`confidence_score`**: A value from 0-100 representing data reliability.
    *   *Example:* A report starts at 50. Adding a valid image adds +20. Being a duplicate subtracts -25.
*   **`state`**: The operational lifecycle stage:
    *   `reported`: Initial entry.
    *   `verified`: Confirmed by admin or algorithm.
    *   `investigating/assigned`: Operational workflow.
    *   `resolved`: Success state.
    *   `expired`: Cleanup didn't happen in time (30 days).
*   **`image_hash`**: An MD5 fingerprint of the uploaded image. Used to stop users from uploading the same photo multiple times to "spam" a location.

---

## 4. Operational Workflow Summary

1.  **Ingestion:** User submits via `POST /report/`.
2.  **Verification:** The `verification.py` service checks for duplicates and assigns a `confidence_score`.
3.  **Visualization:** The `heatmap_engine.py` processes active reports into weighted JSON for the map.
4.  **Action:** Admins use `PATCH /admin/report/{id}` to move a report through the lifecycle.
5.  **Analytics:** The `analytics_engine.py` runs clustering and frequency analysis to produce the dashboard data.
```

### Overview of Key Concepts

1.  **Separation of Concerns:** Notice that **Severity** (how bad the trash is) and **State** (what we are doing about it) are completely separate. A "Critical" incident remains critical even when it is "Assigned" to a team.
2.  **The 30-Day Rule:** To prevent the database from feeling "cluttered" with old data, the background job in `main.py` (the `auto_expiry_job`) automatically moves reports to the `expired` state if they haven't been resolved within 30 days. This keeps the heatmap fresh.
3.  **Duplicate Handling:** We don't delete duplicates. We store them, but we flag them with `is_duplicate = True`. This allows admins to see that multiple people are complaining about the same thing, which actually *increases* the confidence of the original report.


