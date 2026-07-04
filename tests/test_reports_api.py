"""
Integration tests for reports API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


def test_root_endpoint(client: TestClient):
    """
    Test the root endpoint returns a status message.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "Waste Management Monitoring API" in response.text


def test_create_report_success(client: TestClient, sample_report_data: dict):
    """
    Test successful report creation with valid data.
    """
    response = client.post("/report/", json=sample_report_data)
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == sample_report_data["latitude"]
    assert data["state"] == "reported"
    assert "confidence_score" in data
    assert data["severity_score"] == 80  # "High" maps to 80


def test_create_report_missing_fields(client: TestClient):
    """
    Test report creation fails with missing required fields.
    """
    incomplete_data = {
        "latitude": 40.7128,
        "longitude": -74.0060
        # Missing location_name, description, severity
    }
    response = client.post("/report/", json=incomplete_data)
    assert response.status_code == 422  # Validation error


def test_create_report_invalid_coordinates(client: TestClient, sample_report_data: dict):
    """
    Test report creation fails with invalid latitude/longitude.
    """
    invalid_data = sample_report_data.copy()
    invalid_data["latitude"] = 999  # Out of range
    response = client.post("/report/", json=invalid_data)
    assert response.status_code == 422


def test_create_report_invalid_severity(client: TestClient, sample_report_data: dict):
    """
    Test report creation with invalid severity level.
    """
    invalid_data = sample_report_data.copy()
    invalid_data["severity"] = "InvalidLevel"
    response = client.post("/report/", json=invalid_data)
    assert response.status_code == 422


def test_create_report_short_description(client: TestClient, sample_report_data: dict):
    """
    Test report creation fails with description < 10 chars.
    """
    invalid_data = sample_report_data.copy()
    invalid_data["description"] = "short"  # Too short
    response = client.post("/report/", json=invalid_data)
    assert response.status_code == 422


def test_create_report_long_description(client: TestClient, sample_report_data: dict):
    """
    Test report creation fails with description > 1000 chars.
    """
    invalid_data = sample_report_data.copy()
    invalid_data["description"] = "a" * 1001  # Too long
    response = client.post("/report/", json=invalid_data)
    assert response.status_code == 422


def test_retrieve_report_by_id(client: TestClient, sample_report_data: dict):
    """
    Test retrieving a report by ID.
    """
    # Create report
    create_response = client.post("/report/", json=sample_report_data)
    if create_response.status_code != 200:
        pytest.skip("Could not create test report")
    
    report_id = create_response.json()["id"]
    
    # Retrieve it
    get_response = client.get(f"/report/{report_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == report_id
    assert data["location_name"] == sample_report_data["location_name"]


def test_retrieve_nonexistent_report(client: TestClient):
    """
    Test retrieving a report that doesn't exist returns 404.
    """
    response = client.get("/report/99999")
    assert response.status_code == 404


def test_heatmap_endpoint(client: TestClient, sample_report_data: dict):
    """
    Test heatmap endpoint returns weighted coordinates.
    """
    # Create a report
    create_response = client.post("/report/", json=sample_report_data)
    if create_response.status_code != 200:
        pytest.skip("Could not create test report")
    
    # Get heatmap
    response = client.get("/heatmap/?min_confidence=40&max_age_days=14")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    if len(data) > 0:
        point = data[0]
        assert "lat" in point
        assert "lon" in point
        assert "weight" in point


def test_heatmap_invalid_params(client: TestClient):
    """
    Test heatmap endpoint rejects invalid parameters.
    """
    response = client.get("/heatmap/?min_confidence=999")  # Out of range
    assert response.status_code == 422
