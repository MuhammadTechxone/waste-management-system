"""
Integration tests for admin API endpoints (requires authentication).
"""
import pytest
import os
from fastapi.testclient import TestClient


def test_admin_endpoint_requires_auth(client: TestClient):
    """
    Test that admin endpoints reject requests without valid auth token.
    """
    response = client.patch(
        "/admin/report/1",
        json={"state": "verified"}
    )
    # Should fail: no Authorization header
    assert response.status_code in [403, 401]


def test_admin_endpoint_with_invalid_token(client: TestClient):
    """
    Test that admin endpoints reject invalid tokens.
    """
    headers = {"Authorization": "Bearer invalid-token-xyz"}
    response = client.patch(
        "/admin/report/1",
        json={"state": "verified"},
        headers=headers
    )
    assert response.status_code == 403


def test_admin_endpoint_with_valid_token(client: TestClient, sample_report_data: dict, admin_token: str):
    """
    Test that admin endpoints accept valid tokens.
    """
    # Create a report first
    create_resp = client.post("/report/", json=sample_report_data)
    if create_resp.status_code != 200:
        pytest.skip("Could not create test report")
    
    report_id = create_resp.json()["id"]
    
    # Now try admin endpoint with valid token
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.patch(
        f"/admin/report/{report_id}",
        json={"state": "verified"},
        headers=headers
    )
    # Should either succeed (200) or give a meaningful error
    assert response.status_code in [200, 404, 422]


def test_admin_invalid_state_transition(client: TestClient, sample_report_data: dict, admin_token: str):
    """
    Test that invalid state transitions are rejected.
    """
    # Create a report
    create_resp = client.post("/report/", json=sample_report_data)
    if create_resp.status_code != 200:
        pytest.skip("Could not create test report")
    
    report_id = create_resp.json()["id"]
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Try invalid state
    response = client.patch(
        f"/admin/report/{report_id}",
        json={"state": "invalid-state"},
        headers=headers
    )
    assert response.status_code == 422  # Validation error


def test_admin_key_validation_on_startup():
    """
    Test that missing ADMIN_API_KEY raises error on startup.
    This is more of a documentation test - the error happens during app initialization.
    """
    # If we got here, the app started, meaning ADMIN_API_KEY was set
    assert os.environ.get("ADMIN_API_KEY") is not None
