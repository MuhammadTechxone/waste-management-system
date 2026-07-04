# Testing Guide

## Running Tests Locally

### Prerequisites
```bash
pip install -r requirements.txt
```

### Set Required Environment Variables
```bash
export ADMIN_API_KEY="your-secure-admin-key-here"
export GOOGLE_API_KEY="your-google-ai-key-here"
```

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_reports_api.py -v
```

### Run Specific Test
```bash
pytest tests/test_reports_api.py::test_create_report_success -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Tests in Watch Mode (requires pytest-watch)
```bash
pip install pytest-watch
ptw tests/
```

## Test Structure

```
tests/
├── __init__.py                # Package marker
├── conftest.py               # Shared fixtures (test DB, test client, sample data)
├── test_reports_api.py       # Integration tests for public API endpoints
├── test_admin_api.py         # Integration tests for admin endpoints with authentication
└── test_security.py          # Security and input validation tests
```

### Test Fixtures (conftest.py)

- **test_db** – In-memory SQLite database, recreated for each test
- **client** – FastAPI TestClient with test DB dependency injected
- **sample_report_data** – Factory for creating valid test report data
- **admin_token** – Mock admin token for protected endpoints

### Test Coverage Goals

- **Target:** ≥70% code coverage
- **Critical Paths:** API endpoints, auth, verification service
- **Checked by:** GitHub Actions on every push

## CI/CD Pipeline

GitHub Actions automatically runs tests on every push to `main`, `develop`, or `feature/**` branches.

**Workflow:**
1. **Lint:** black, flake8 (warnings only, doesn't fail)
2. **Type Check:** mypy (optional)
3. **Tests:** pytest with coverage
4. **Coverage Upload:** codecov
5. **Docker Build:** Build image to catch Dockerfile issues

### View Results

- GitHub: **Actions** tab → workflow run → test job output
- Coverage: codecov.io (if integrated)

## Mocking External Services

For tests that require Google Generative AI or other external APIs:

```python
from unittest.mock import patch

@patch('services.verification.classify_image')
def test_with_mock_classifier(mock_classifier):
    mock_classifier.return_value = {
        "type": "garbage",
        "confidence": 0.95
    }
    # Test code here
```

## Common Issues

### ImportError: No module named 'main'
**Solution:** Make sure you're running pytest from the project root:
```bash
cd /path/to/waste-management-system
pytest tests/
```

### ADMIN_API_KEY not set
**Solution:** Set the environment variable before running tests:
```bash
export ADMIN_API_KEY="test-admin-key-secure-1234567890"
pytest tests/
```

### Database locked (SQLite)
**Solution:** Each test gets a fresh in-memory database. If you see this, clear pytest cache:
```bash
rm -rf .pytest_cache/
pytest tests/
```

## Adding New Tests

1. Create a new file in `tests/` named `test_<feature>.py`
2. Import fixtures from `conftest.py`
3. Write test functions following the pattern:
   ```python
   def test_my_feature(client: TestClient, sample_report_data: dict):
       """Test description."""
       response = client.post("/endpoint/", json=sample_report_data)
       assert response.status_code == 200
   ```
4. Run the test: `pytest tests/test_my_feature.py::test_my_feature -v`

## Performance Tips

- Use `pytest -x` to stop at first failure
- Use `pytest -k test_name` to run tests matching a pattern
- Use `pytest --tb=short` for shorter tracebacks
- Use `pytest -q` for quiet mode (fewer details)

## Documentation

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
