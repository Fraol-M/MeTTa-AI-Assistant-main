"""
Unit tests for authentication services.
"""
import pytest
from unittest.mock import AsyncMock, patch
from jose import jwt, ExpiredSignatureError
from passlib.context import CryptContext
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_secret_key,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    pwd_context
)


@pytest.mark.unit
class TestAuthService:
    """Test authentication service functions."""

    def test_get_secret_key(self):
        """Test that secret key is retrieved from environment."""
        with patch('app.services.auth.os.getenv', return_value="test-secret-key"):
            key = get_secret_key()
            assert key == "test-secret-key"

    def test_get_secret_key_missing(self):
        """Test that RuntimeError is raised when secret key is missing."""
        with patch('app.services.auth.os.getenv', return_value=None):
            with pytest.raises(RuntimeError, match="JWT_SECRET"):
                get_secret_key()

    def test_create_access_token(self):
        """Test access token creation."""
        with patch('app.services.auth.get_secret_key', return_value="test-secret"):
            with patch('app.services.auth.time.time', return_value=1000):
                data = {"sub": "user123", "role": "user"}
                token = create_access_token(data)
                
                # Decode and verify
                decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])
                assert decoded["sub"] == "user123"
                assert decoded["role"] == "user"
                assert decoded["exp"] == 1000 + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        with patch('app.services.auth.get_secret_key', return_value="test-secret"):
            with patch('app.services.auth.time.time', return_value=1000):
                data = {"sub": "user123", "role": "user"}
                token = create_refresh_token(data)
                
                # Decode and verify
                decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])
                assert decoded["sub"] == "user123"
                assert decoded["role"] == "user"
                assert decoded["type"] == "refresh"
                assert decoded["exp"] == 1000 + (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, mock_mongo_collection):
        """Test successful user authentication."""
        test_password = "testpassword123"
        hashed = pwd_context.hash(test_password)
        
        mock_user = {
            "_id": "507f1f77bcf86cd799439011",
            "email": "test@example.com",
            "hashed_password": hashed,
            "role": "user"
        }
        
        mock_mongo_collection.find_one = AsyncMock(return_value=mock_user)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        user = await authenticate_user("test@example.com", test_password, mock_db)
        
        assert user is not None
        assert user["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, mock_mongo_collection):
        """Test authentication with wrong password."""
        test_password = "testpassword123"
        hashed = pwd_context.hash(test_password)
        
        mock_user = {
            "_id": "507f1f77bcf86cd799439011",
            "email": "test@example.com",
            "hashed_password": hashed,
            "role": "user"
        }
        
        mock_mongo_collection.find_one = AsyncMock(return_value=mock_user)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        user = await authenticate_user("test@example.com", "wrongpassword", mock_db)
        
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, mock_mongo_collection):
        """Test authentication when user doesn't exist."""
        mock_mongo_collection.find_one = AsyncMock(return_value=None)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        user = await authenticate_user("nonexistent@example.com", "password", mock_db)
        
        assert user is None

