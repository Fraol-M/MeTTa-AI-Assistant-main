# Test Suite Documentation

This directory contains comprehensive tests for the MeTTa AI Assistant backend.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── unit/                    # Unit tests (isolated component tests)
│   ├── test_auth.py        # Authentication service tests
│   └── test_db.py          # Database operation tests
├── integration/            # Integration tests (API endpoints)
│   ├── test_auth_endpoints.py
│   ├── test_chunk_endpoints.py
│   ├── test_protected_endpoints.py
│   └── test_middleware.py
└── README.md               # This file
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run unit tests only
```bash
pytest tests/unit -v
```

### Run integration tests only
```bash
pytest tests/integration -v
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/unit/test_auth.py -v
```

### Run specific test
```bash
pytest tests/unit/test_auth.py::TestAuthService::test_create_access_token -v
```

## Test Markers

Tests are organized with markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow running tests

Run tests by marker:
```bash
pytest -m unit
pytest -m integration
```

## Environment Variables for Testing

Set these environment variables for testing:
- `JWT_SECRET` - Secret key for JWT tokens
- `MONGO_URI` - MongoDB connection string
- `MONGO_DB` - Test database name
- `QDRANT_HOST` - Qdrant host
- `QDRANT_PORT` - Qdrant port
- `COLLECTION_NAME` - Qdrant collection name
- `ADMIN_EMAIL` - Admin user email
- `ADMIN_PASSWORD` - Admin user password

## CI/CD

Tests run automatically on:
- Push to main/develop branches
- Pull requests to main/develop branches

See `.github/workflows/ci.yml` for CI configuration.

## Coverage

Coverage reports are generated in:
- Terminal: `pytest --cov=app`
- HTML: `pytest --cov=app --cov-report=html` (see `htmlcov/index.html`)
- XML: `pytest --cov=app --cov-report=xml` (for CI)

Minimum coverage threshold: 60%

