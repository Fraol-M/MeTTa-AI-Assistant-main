"""
Shared fixtures and test configuration for pytest.
"""
import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from typing import AsyncGenerator
from jose import jwt
from datetime import datetime, timedelta
from pymongo.database import Database
from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer

from app.main import app
from app.db.users import UserRole


# Test database configuration
TEST_MONGO_URI = os.getenv("TEST_MONGO_URI", "mongodb://localhost:27017")
TEST_MONGO_DB = os.getenv("TEST_MONGO_DB", "metta_test_db")
TEST_QDRANT_HOST = os.getenv("TEST_QDRANT_HOST", "localhost")
TEST_QDRANT_PORT = int(os.getenv("TEST_QDRANT_PORT", "6333"))
TEST_COLLECTION_NAME = "test_collection"
TEST_JWT_SECRET = "test-secret-key-for-testing-only-change-in-production"


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Set test environment variables."""
    os.environ["JWT_SECRET"] = TEST_JWT_SECRET
    os.environ["MONGO_URI"] = TEST_MONGO_URI
    os.environ["MONGO_DB"] = TEST_MONGO_DB
    os.environ["QDRANT_HOST"] = TEST_QDRANT_HOST
    os.environ["QDRANT_PORT"] = str(TEST_QDRANT_PORT)
    os.environ["COLLECTION_NAME"] = TEST_COLLECTION_NAME
    os.environ["ADMIN_EMAIL"] = "admin@test.com"
    os.environ["ADMIN_PASSWORD"] = "test_admin_password"
    yield
    # Cleanup if needed


@pytest.fixture
def mock_mongo_db():
    """Mock MongoDB database."""
    db = AsyncMock(spec=Database)
    db.command = AsyncMock(return_value={"ok": 1})
    return db


@pytest.fixture
def mock_mongo_collection():
    """Mock MongoDB collection."""
    collection = AsyncMock()
    collection.find_one = AsyncMock(return_value=None)
    collection.find = AsyncMock()
    collection.insert_one = AsyncMock()
    collection.insert_many = AsyncMock()
    collection.update_one = AsyncMock()
    collection.update_many = AsyncMock()
    collection.delete_one = AsyncMock()
    collection.delete_many = AsyncMock()
    return collection


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client."""
    client = AsyncMock(spec=AsyncQdrantClient)
    client.search = AsyncMock(return_value=[])
    client.upsert = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_embedding_model():
    """Mock SentenceTransformer model."""
    model = MagicMock(spec=SentenceTransformer)
    model.encode = MagicMock(return_value=[[0.1] * 384])  # Mock embedding vector
    return model


@pytest.fixture
def test_user_data():
    """Sample test user data."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "role": UserRole.USER
    }


@pytest.fixture
def test_admin_data():
    """Sample test admin data."""
    return {
        "email": "admin@test.com",
        "password": "adminpassword123",
        "role": UserRole.ADMIN
    }


@pytest.fixture
def test_token_payload():
    """Test JWT token payload."""
    return {
        "sub": "507f1f77bcf86cd799439011",
        "role": "user",
        "exp": int((datetime.utcnow() + timedelta(minutes=15)).timestamp())
    }


@pytest.fixture
def test_token(test_token_payload):
    """Generate test JWT token."""
    return jwt.encode(test_token_payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def admin_token():
    """Generate test admin JWT token."""
    payload = {
        "sub": "507f1f77bcf86cd799439011",
        "role": "admin",
        "exp": int((datetime.utcnow() + timedelta(minutes=15)).timestamp())
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def expired_token():
    """Generate expired test JWT token."""
    payload = {
        "sub": "507f1f77bcf86cd799439011",
        "role": "user",
        "exp": int((datetime.utcnow() - timedelta(minutes=1)).timestamp())
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture
def client(mock_mongo_db, mock_qdrant_client, mock_embedding_model):
    """Create test client with mocked dependencies."""
    # Set up app.state with mocked dependencies
    app.state.mongo_db = mock_mongo_db
    app.state.qdrant_client = mock_qdrant_client
    app.state.embedding_model = mock_embedding_model
    return TestClient(app)


@pytest.fixture
async def async_client(
    mock_mongo_db, mock_qdrant_client, mock_embedding_model
) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with mocked dependencies."""
    # Set up app.state with mocked dependencies
    app.state.mongo_db = mock_mongo_db
    app.state.qdrant_client = mock_qdrant_client
    app.state.embedding_model = mock_embedding_model
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_app_state(mock_mongo_db, mock_qdrant_client, mock_embedding_model):
    """Mock app.state with all dependencies."""
    with patch('app.main.app.state') as mock_state:
        mock_state.mongo_client = AsyncMock()
        mock_state.mongo_db = mock_mongo_db
        mock_state.qdrant_client = mock_qdrant_client
        mock_state.embedding_model = mock_embedding_model
        yield mock_state


@pytest.fixture
def sample_chunk_data():
    """Sample chunk data for testing."""
    return {
        "chunkId": "test_chunk_123",
        "source": "code",
        "chunk": "This is a test chunk of code.",
        "isEmbedded": False,
        "project": "test_project",
        "repo": "test_repo",
        "section": ["function1"],
        "file": ["test.metta"],
        "version": "1.0.0"
    }


@pytest.fixture
def sample_doc_chunk_data():
    """Sample documentation chunk data."""
    return {
        "chunkId": "doc_chunk_456",
        "source": "documentation",
        "chunk": "This is a documentation chunk.",
        "isEmbedded": False,
        "url": "https://example.com/docs",
        "page_title": "Test Documentation",
        "category": "guides"
    }

