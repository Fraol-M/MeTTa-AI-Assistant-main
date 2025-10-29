# Testing Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   cd Backend
   pip install -r requirements.txt
   ```

2. **Run all tests:**
   ```bash
   pytest
   ```

3. **Run with coverage:**
   ```bash
   pytest --cov=app --cov-report=html
   ```

## Test Coverage

Our test suite includes:

### Unit Tests (`tests/unit/`)
- **Authentication Services** (`test_auth.py`)
  - Token creation and validation
  - User authentication
  - Password hashing verification

- **Database Operations** (`test_db.py`)
  - CRUD operations for chunks
  - User management
  - Embedding status updates

### Integration Tests (`tests/integration/`)
- **API Endpoints** (`test_auth_endpoints.py`, `test_chunk_endpoints.py`)
  - Authentication endpoints (signup, login, refresh)
  - Chunk management endpoints
  - Embedding pipeline
  - Semantic search

- **Middleware** (`test_middleware.py`)
  - JWT token validation
  - Protected route access
  - Role-based access control

- **Protected Endpoints** (`test_protected_endpoints.py`)
  - Admin-only routes
  - User role validation

## CI/CD

Tests automatically run on:
- ✅ Every push to `main` or `develop` branches
- ✅ Every pull request to `main` or `develop` branches

The CI pipeline:
1. Sets up Python 3.11
2. Starts MongoDB and Qdrant services
3. Installs dependencies
4. Runs unit tests
5. Runs integration tests
6. Generates coverage reports
7. Uploads coverage to Codecov (optional)

View CI status in the GitHub Actions tab of your repository.

## Local Testing Requirements

For local testing, you'll need:

1. **MongoDB** running locally (optional - tests use mocks)
2. **Qdrant** running locally (optional - tests use mocks)

Alternatively, most tests use mocked dependencies, so external services aren't required for unit tests.

## Test Configuration

Test configuration is in:
- `pytest.ini` - Pytest configuration
- `.coveragerc` - Coverage configuration
- `tests/conftest.py` - Shared fixtures

## Writing New Tests

1. **Unit Tests**: Add to `tests/unit/`
2. **Integration Tests**: Add to `tests/integration/`
3. **Mark tests**: Use `@pytest.mark.unit`, `@pytest.mark.integration`
4. **Use fixtures**: Check `conftest.py` for available fixtures

Example:
```python
import pytest

@pytest.mark.unit
def test_my_function():
    assert my_function() == expected_result

@pytest.mark.integration
async def test_my_endpoint(async_client):
    response = await async_client.get("/api/my-endpoint")
    assert response.status_code == 200
```

## Coverage Goals

- Current threshold: 60% (configurable in `pytest.ini`)
- Target: 80%+ for production

