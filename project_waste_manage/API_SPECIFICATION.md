# Waste Management API Technical Specification

## 1. Authentication
*   **Public Endpoints:** No headers required.
*   **Admin Endpoints:** Requires header `Authorization: Bearer <ADMIN_API_KEY>`.

---

## 2. Public User Endpoints

### 2.1 Submit Waste Report
*   **Endpoint:** `POST /report/`
*   **Format:** `multipart/form-data`
*   **Inputs:**
    *   `latitude` (float): GPS Latitude.
    *   `longitude` (float): GPS Longitude.
    *   `location_name` (string): Area name.
    *   `description` (string): Details (min 10 chars).
    *   `severity` (string): `Low` | `Medium` | `High` | `Critical`.
    *   `reporter_id` (string, optional): Unique device/user ID.
    *   `image` (file, optional): Binary image (JPG/PNG), max 5MB.
*   **Response (201):**
    ```json
    { "success": true, "report_id": 1, "state": "reported", "confidence_score": 75 }
    ```

### 2.2 View Reports (Public Feed)
*   **Endpoint:** `GET /report/`
*   **Query Params:** `severity`, `state`, `radius_km`, `lat`, `lon`, `page`, `limit`.
*   **Response:** `List[ReportResponse]`

### 2.3 Visual Heatmap
*   **Endpoint:** `GET /heatmap/`
*   **Query Params:** `min_confidence` (default 40), `max_age_days` (default 14).
*   **Response:** `List[{"lat": float, "lon": float, "weight": float}]`

### 2.4 Environmental Alerts
*   **Endpoint:** `GET /alerts/`
*   **Query Params:** `severity_min` (default "High"), `lat`, `lon`, `radius_km`.
*   **Response:** `List[{"alert_type": "string", "message": "string", "centroid": dict}]`

---

## 3. Admin Endpoints (Auth Required)

### 3.1 Admin Report Management
*   **Endpoint:** `GET /admin/reports`
*   **Purpose:** Detailed view including image paths and duplicate flags.
*   **Response:** `List[AdminReportResponse]`

### 3.2 Update Incident State
*   **Endpoint:** `PATCH /admin/report/{report_id}`
*   **Format:** `application/json`
*   **Body:**
    ```json
    { "state": "verified" }
    ```
*   **Valid State Transitions:**
    *   `reported` -> `verified`, `rejected`, `expired`
    *   `verified` -> `investigating`, `rejected`
    *   `investigating` -> `assigned`, `rejected`
    *   `assigned` -> `resolved`, `investigating`

### 3.3 Dashboard Analytics
*   **Endpoint:** `GET /admin/analytics/`
*   **Response:**
    ```json
    {
      "unresolved_count": 10,
      "cleanup_efficiency_pct": 85.5,
      "avg_resolve_days": 2.1,
      "severity_distribution": { "High": 40.0, ... },
      "top_areas": [...],
      "daily_frequency": [...],
      "recurring_hotspots": [...]
    }
    ```

---

## 4. Data Models (JSON reference)

### ReportResponse
```json
{
  "id": 101,
  "latitude": 9.057,
  "longitude": 7.495,
  "location_name": "Central Square",
  "description": "Large waste pile near gate",
  "severity": "High",
  "severity_score": 80,
  "state": "reported",
  "confidence_score": 85,
  "created_at": "2026-05-19T12:00:00Z"
}
```

### AdminReportResponse (Includes sensitive data)
```json
{
  ...ReportResponse,
  "image_path": "uploads/2026-05-19/uuid.jpg",
  "is_duplicate": false,
  "reporter_id": "user_99"
}
```

## 5. Error Codes
*   `400`: Bad Request (Invalid severity level).
*   `403`: Forbidden (Invalid Admin API Key).
*   `409`: Conflict (Illegal state transition).
*   `413`: Payload Too Large (Image > 5MB).
*   `422`: Validation Error (Malformed coordinates).