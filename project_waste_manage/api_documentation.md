# Waste Management Monitoring System — API Documentation

This document provides the necessary information for frontend integration with the Waste Management Backend.

**Base URL:** `https://<your-username>-<your-space-name>.hf.space`

---

## 1. Authentication

Public endpoints do not require authentication. Admin endpoints require a Bearer Token.

*   **Header:** `Authorization: Bearer <ADMIN_API_KEY>`

---

## 2. Public Endpoints

### 2.1 Submit a Report
`POST /report/`

**Format:** `multipart/form-data`

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `latitude` | Float | Yes | GPS Latitude (-90 to 90) |
| `longitude` | Float | Yes | GPS Longitude (-180 to 180) |
| `location_name` | String | Yes | Human-readable location |
| `description` | String | Yes | Minimum 10 characters recommended |
| `severity` | String | Yes | `Low`, `Medium`, `High`, `Critical` |
| `reporter_id` | String | No | Unique ID for the reporting device/user |
| `image` | File | No | Image file (JPG, PNG, WEBP). Max 5MB |

**Example Success Response (201 Created):**
```json
{
  "success": true,
  "report_id": 12,
  "severity": "High",
  "state": "reported",
  "confidence_score": 85
}
```

---

### 2.2 List Reports
`GET /report/`

Retrieve reports with optional filtering.

**Query Parameters:**
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `severity` | String | null | Filter by severity level |
| `state` | String | null | Filter by comma-separated states (e.g., `verified,assigned`) |
| `exclude_resolved`| Boolean | true | Hides resolved, rejected, or expired reports |
| `lat` | Float | null | Center latitude for proximity search |
| `lon` | Float | null | Center longitude for proximity search |
| `radius_km` | Float | null | Search radius around lat/lon |
| `page` | Integer | 1 | Pagination page number |
| `limit` | Integer | 50 | Results per page (Max 200) |

**Response Body:** `List[ReportResponse]`
```json
[
  {
    "latitude": 9.0579,
    "longitude": 7.4951,
    "location_name": "Wuse Market",
    "description": "Blocked drainage",
    "severity": "High",
    "id": 12,
    "state": "reported",
    "severity_score": 80,
    "confidence_score": 85,
    "created_at": "2026-05-18T14:30:00"
  }
]
```

---

### 2.3 Heatmap Data
`GET /heatmap/`

Weighted coordinates for mapping libraries (Leaflet/Mapbox).

**Query Parameters:**
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `min_confidence` | Int | 40 | Minimum confidence to include |
| `max_age_days` | Int | 14 | Exclude reports older than this |
| `include_resolved`| Boolean | false | If true, resolved reports weigh 10% |

**Response Body:**
```json
[
  { "lat": 9.0579, "lon": 7.4951, "weight": 48.0 }
]
```

---

### 2.4 Environmental Alerts
`GET /alerts/`

High-risk accumulation zones based on report clusters.

**Query Parameters:**
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `severity_min` | String | "High" | Minimum severity to trigger alert |
| `lat` | Float | null | User latitude |
| `lon` | Float | null | User longitude |
| `radius_km` | Float | 5.0 | Proximity radius for alerts |

**Response Body:**
```json
[
  {
    "alert_type": "Environmental Risk Hotspot",
    "message": "Significant waste accumulation (12 reports) detected.",
    "centroid": { "lat": 9.0579, "lon": 7.4951 },
    "severity_score": 80
  }
]
```

---

## 3. Admin Endpoints (Requires Auth)

### 3.1 Admin Report View
`GET /admin/reports`

**Query Parameters:** `state`, `severity`.

**Response Body:** `List[AdminReportResponse]`
Includes `image_path`, `image_hash`, and `is_duplicate` flag.

---

### 3.2 Update Report State
`PATCH /admin/report/{report_id}`

**JSON Body:**
```json
{
  "state": "investigating"
}
```

**Valid States:** `reported`, `verified`, `investigating`, `assigned`, `resolved`, `rejected`, `expired`.

**State Transition Rules:**
*   `reported` → `verified`, `rejected`, `expired`
*   `verified` → `investigating`, `rejected`
*   `investigating` → `assigned`, `rejected`
*   `assigned` → `resolved`, `investigating`

---

### 3.3 Dashboard Analytics
`GET /admin/analytics/`

**Response Body:**
```json
{
  "generated_at": "2026-05-18T23:00:00",
  "unresolved_count": 45,
  "cleanup_efficiency_pct": 72.5,
  "avg_resolve_days": 3.4,
  "severity_distribution": {
    "Low": 10.0,
    "Medium": 40.0,
    "High": 35.0,
    "Critical": 15.0
  },
  "top_areas": [
    {
      "centroid_lat": 9.057,
      "centroid_lon": 7.495,
      "report_ids": [1, 5, 8],
      "size": 3,
      "max_severity": 80
    }
  ]
}
```

---

## 4. Common Error Codes

| Code | Name | Description |
| :--- | :--- | :--- |
| 200 | OK | Request succeeded. |
| 201 | Created | Report submitted successfully. |
| 400 | Bad Request | Invalid input parameters. |
| 403 | Forbidden | Invalid or missing Admin API Key. |
| 404 | Not Found | Resource or endpoint does not exist. |
| 409 | Conflict | Invalid state transition attempted. |
| 413 | Payload Too Large| Image file exceeds 5MB. |
| 422 | Unprocessable | Validation error (check latitude/longitude ranges). |

---

## 5. Metadata

*   **Images:** Stored as static files. To serve them, configure FastAPI static files mounting or use the full object storage URL.
*   **Pagination:** Use `page` and `limit` on `/report/` and `/admin/reports`.
*   **CORS:** Allowed for `*.hf.space` and `localhost`.