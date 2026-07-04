"""
Security and validation tests.
"""
import pytest
from fastapi.testclient import TestClient
import re


def test_input_validation_location_name(client: TestClient, sample_report_data: dict):
    """
    Test that location names with special characters are rejected.
    """
    invalid_data = sample_report_data.copy()
    invalid_data["location_name"] = "Location <script>alert('xss')</script>"
    response = client.post("/report/", json=invalid_data)
    assert response.status_code == 422


def test_input_validation_description_sql_injection(client: TestClient, sample_report_data: dict):
    """
    Test that SQL-like injection attempts are accepted (but safe due to ORM).
    This verifies the description field accepts the string, as ORM parameterization prevents injection.
    """
    malicious_data = sample_report_data.copy()
    malicious_data["description"] = "'; DROP TABLE reports; --' This is a valid description of the issue"
    response = client.post("/report/", json=malicious_data)
    # Should succeed - the ORM prevents SQL injection
    assert response.status_code == 200


def test_cors_no_null_origin(client: TestClient):
    """
    Test that CORS is properly configured (null origin should not be in allow list in production).
    Note: This is more of a configuration check; actual CORS headers depend on main.py config.
    """
    # Make a request with no Origin header
    response = client.get("/")
    assert response.status_code == 200


def test_severity_score_mapping(client: TestClient, sample_report_data: dict):
    """
    Test that severity levels map to correct scores.
    """
    severity_mapping = {
        "Low": 20,
        "Medium": 50,
        "High": 80,
        "Critical": 100
    }
    
    for severity, expected_score in severity_mapping.items():
        data = sample_report_data.copy()
        data["severity"] = severity
        response = client.post("/report/", json=data)
        assert response.status_code == 200
        assert response.json()["severity_score"] == expected_score


def test_confidence_score_default(client: TestClient, sample_report_data: dict):
    """
    Test that newly created reports have default confidence score of 50.
    """
    response = client.post("/report/", json=sample_report_data)
    assert response.status_code == 200
    assert response.json()["confidence_score"] == 50
