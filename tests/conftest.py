"""
Shared pytest fixtures: test database, FastAPI test client, sample data.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import models
from database import Base, get_db
from main import app

# In-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    """
    Create an isolated in-memory test database for each test.
    """
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def client(test_db: Session):
    """
    FastAPI test client with test database dependency injected.
    """
    return TestClient(app)

@pytest.fixture
def sample_report_data():
    """
    Factory for creating test report data.
    """
    return {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "location_name": "Times Square, NYC",
        "description": "Pile of garbage near the corner of the street",
        "severity": "High"
    }

@pytest.fixture
def admin_token():
    """
    Mock admin token for testing protected endpoints.
    """
    # Set test admin key
    test_key = "test-admin-key-secure-1234567890"
    os.environ["ADMIN_API_KEY"] = test_key
    return test_key
